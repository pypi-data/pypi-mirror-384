# Copyright 2022 Karlsruhe Institute of Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from copy import deepcopy
from io import BytesIO
from urllib.parse import quote

from flask import current_app
from flask_login import current_user
from rdflib import DCTERMS
from rdflib import OWL
from rdflib import RDF
from rdflib import SH
from rdflib import XSD
from rdflib import BNode
from rdflib import Literal
from rdflib import Namespace
from rdflib import URIRef
from rdflib.collection import Collection as RDFCollection

import kadi.lib.constants as const
from kadi.lib.export import RDFGraph
from kadi.lib.utils import formatted_json
from kadi.lib.web import url_for
from kadi.modules.records.export import filter_extras
from kadi.modules.records.extras import is_nested_type

from .models import TemplateType
from .schemas import TemplateSchema


JSON_SCHEMA_TYPE_MAPPING = {
    "str": {"type": "string", "minLength": 1},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "date": {"type": "string", "format": "date-time"},
}

XSD_TYPE_MAPPING = {
    "str": XSD.string,
    "int": XSD.integer,
    "float": XSD.float,
    "bool": XSD.boolean,
    "date": XSD.dateTime,
}


class TemplateShaclGraph(RDFGraph):
    """Template SHACL shapes graph export class.

    See :func:`get_export_data` for an explanation of the parameters.
    """

    def __init__(self, template, export_filter=None, user=None):
        super().__init__()

        export_filter = export_filter if export_filter is not None else {}
        user = user if user is not None else current_user

        self.template_ns = Namespace(
            url_for("templates.view_template", id=template.id, _anchor="")
        )
        self.bind(f"k4m{template.id}", self.template_ns)

        self._add_metadata(template, export_filter, user)

    def _add_metadata(self, template, export_filter, user):
        template_data = get_dict_data(template, export_filter, user)
        template_ref = URIRef(url_for("templates.view_template", id=template.id))

        self.add((template_ref, RDF.type, SH.NodeShape))
        self.add(
            (template_ref, DCTERMS.title, Literal(template_data["title"], lang="en"))
        )
        self.add(
            (
                template_ref,
                DCTERMS.created,
                Literal(template_data["created_at"], datatype=XSD.date),
            )
        )

        if description := template_data["description"]:
            self.add(
                (template_ref, DCTERMS.description, Literal(description, lang="en"))
            )

        if "creator" in template_data:
            user_data = template_data["creator"]

            if orcid := user_data["orcid"]:
                author_ref = URIRef(f"{const.URL_ORCID}/{orcid}")
            else:
                author_ref = URIRef(url_for("accounts.view_user", id=user_data["id"]))

            self.add((template_ref, DCTERMS.creator, author_ref))

        extra_metadata = None

        if template.type == TemplateType.RECORD:
            extra_metadata = template_data["data"].get("extras", [])

        elif template.type == TemplateType.EXTRAS:
            extra_metadata = template_data["data"]

        if extra_metadata:
            self._add_extra_metadata(extra_metadata, template_ref)

    def _add_extra_metadata(self, extras, current_ref, key_prefix=""):
        for index, extra in enumerate(extras):
            extras_node = BNode()
            self.add((current_ref, SH.property, extras_node))

            key = extra.get("key", str(index))
            prefixed_key = f"{key_prefix}{key}"
            extra_ref = self.template_ns[quote(prefixed_key, safe="")]

            self.add((extras_node, SH.name, Literal(key, lang="en")))
            self.add((extras_node, SH.order, Literal(index)))
            self.add((extras_node, SH.maxCount, Literal(1)))

            if "term" in extra:
                self.add((extras_node, SH.path, URIRef(extra["term"])))
            else:
                self.add((extras_node, SH.path, extra_ref))

            if "description" in extra:
                self.add(
                    (
                        extras_node,
                        SH.description,
                        Literal(extra.get("description"), lang="en"),
                    )
                )

            if is_nested_type(extra["type"]):
                self.add((current_ref, OWL.imports, extra_ref))
                self.add((extras_node, SH.qualifiedValueShape, extra_ref))
                self.add((extra_ref, RDF.type, SH.NodeShape))
                self.add((extra_ref, DCTERMS.title, Literal(key, lang="en")))

                self._add_extra_metadata(
                    extra["value"], extra_ref, key_prefix=f"{prefixed_key}."
                )
            else:
                datatype = XSD_TYPE_MAPPING[extra["type"]]
                validation = extra.get("validation", {})

                if validation.get("iri", False):
                    datatype = XSD.anyURI

                self.add((extras_node, SH.datatype, datatype))

                if (extra_value := extra["value"]) is not None:
                    self.add(
                        (
                            extras_node,
                            SH.defaultValue,
                            Literal(extra_value, datatype=datatype),
                        )
                    )

                if validation.get("required", False):
                    self.add((extras_node, SH.minCount, Literal(1)))

                if "options" in validation:
                    options_node = BNode()
                    option_values = [
                        Literal(option, datatype=datatype)
                        for option in validation["options"]
                    ]

                    RDFCollection(self, options_node, option_values)
                    self.add((extras_node, SH["in"], options_node))

                if "range" in validation:
                    value_range = validation["range"]

                    if (min_value := value_range["min"]) is not None:
                        self.add((extras_node, SH.minInclusive, Literal(min_value)))

                    if (max_value := value_range["max"]) is not None:
                        self.add((extras_node, SH.maxInclusive, Literal(max_value)))


def get_dict_data(template, export_filter, user):
    """Export a template as a dictionary.

    See :func:`get_export_data` for an explanation of the parameters.

    :return: The exported template as a dictionary.
    """

    # Common attributes to exclude in all templates, also depending on whether user
    # information should be excluded.
    exclude_attrs = ["visibility", "plain_description", "state", "_actions", "_links"]

    if export_filter.get("user", False):
        exclude_attrs.append("creator")
    else:
        exclude_attrs += const.EXPORT_EXCLUDE_USER_ATTRS

    # Collect the basic metadata of the template.
    schema = TemplateSchema(exclude=exclude_attrs)
    template_data = schema.dump(template)

    # Exclude any filtered extra metadata, if applicable.
    exclude_extras = export_filter.get("extras")

    if exclude_extras:
        if template.type == TemplateType.RECORD:
            template_data["data"]["extras"] = filter_extras(
                template_data["data"]["extras"], exclude_extras
            )
        elif template.type == TemplateType.EXTRAS:
            template_data["data"] = filter_extras(template_data["data"], exclude_extras)

    return template_data


def get_json_data(template, export_filter, user):
    """Export a template as a JSON file.

    See :func:`get_export_data` for an explanation of the parameters and return value.
    """
    template_data = get_dict_data(template, export_filter, user)
    json_data = formatted_json(template_data)

    return BytesIO(json_data.encode())


def _extras_to_json_schema(extras):
    extras_schema = {}
    required_props = []

    for index, extra in enumerate(extras):
        extra_key = extra.get("key", str(index))

        if is_nested_type(extra["type"]):
            schema, required = _extras_to_json_schema(extra["value"])

            if extra["type"] == "dict":
                extras_schema[extra_key] = {
                    "type": "object",
                    "properties": schema,
                    "propertiesOrder": list(schema.keys()),
                }

                if required:
                    extras_schema[extra_key]["required"] = required
            else:
                # We handle the list as a tuple, so we can support different schemas for
                # all entries that are present.
                extras_schema[extra_key] = {
                    "type": "array",
                    "prefixItems": list(schema.values()),
                }
        else:
            extras_schema[extra_key] = deepcopy(JSON_SCHEMA_TYPE_MAPPING[extra["type"]])

            if (extra_value := extra["value"]) is not None:
                extras_schema[extra_key]["default"] = extra_value

            # We simply add the unit as a custom property in the JSON schema for now to
            # keep the validation of the actual values consistent across types.
            if "unit" in extra:
                extras_schema[extra_key]["unit"] = {"type": "string", "minLength": 1}

                if extra["unit"]:
                    extras_schema[extra_key]["unit"]["default"] = extra["unit"]

            if "validation" in extra:
                validation = extra["validation"]
                required = validation.get("required", False)

                if required:
                    required_props.append(extra_key)

                if "options" in validation:
                    # Make sure we work on a copy of the options list.
                    options = list(validation["options"])
                    extras_schema[extra_key]["enum"] = options

                if "range" in validation:
                    value_range = validation["range"]

                    if (min_value := value_range["min"]) is not None:
                        extras_schema[extra_key]["minimum"] = min_value

                    if (max_value := value_range["max"]) is not None:
                        extras_schema[extra_key]["maximum"] = max_value

        if (extra_description := extra.get("description")) is not None:
            extras_schema[extra_key]["description"] = extra_description

    return extras_schema, required_props


def get_json_schema_data(template, export_filter, user):
    """Export a template as a JSON Schema file in JSON format.

    See :func:`get_export_data` for an explanation of the parameters and return value.
    """
    template_data = get_dict_data(template, export_filter, user)
    extra_metadata = None

    json_schema_data = {"$schema": "https://json-schema.org/draft/2020-12/schema"}

    if template.type == TemplateType.RECORD:
        extra_metadata = template_data["data"].get("extras", [])

    elif template.type == TemplateType.EXTRAS:
        extra_metadata = template_data["data"]

    if extra_metadata:
        schema, required = _extras_to_json_schema(extra_metadata)
        json_schema_data.update(
            {
                "type": "object",
                "properties": schema,
                "propertiesOrder": list(schema.keys()),
            }
        )

        if required:
            json_schema_data["required"] = required

    json_data = formatted_json(json_schema_data)
    return BytesIO(json_data.encode())


def get_shacl_data(template, export_filter, user):
    """Export a template as a SHACL shapes graph.

    See :func:`get_export_data` for an explanation of the parameters and return value.
    """
    shacl_graph = TemplateShaclGraph(template, export_filter=export_filter, user=user)

    try:
        shacl_data = shacl_graph.serialize(format="turtle")
    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        shacl_data = ""

    return BytesIO(shacl_data.encode())


def get_export_data(template, export_type, export_filter=None, user=None):
    """Export a template in a given format.

    :param template: The template to export.
    :param export_type: The export type, one of ``"json"``, ``"json-schema"`` or
        ``"shacl"``.
    :param export_filter: (optional) A dictionary specifying various filters to adjust
        the returned export data, depending on the export and template type.  Note that
        the values in the example below represent the respective default values.

        **Example:**

        .. code-block:: python3

            {
                # Whether user information about the creator of the template should be
                # excluded.
                "user": False,
                # A dictionary specifying a filter mask of extra metadata keys to
                # exclude, e.g. {"sample_key": {}, "sample_list": {"0": {}}}. The value
                # of each key can either be an empty dictionary, to exclude the whole
                # extra, or another dictionary with the same possibilities as in the
                # parent dictionary. For list entries, indices need to be specified as
                # strings, starting at 0.
                "extras": {},
            }


    :param user: (optional) The user to check for various access permissions when
        generating the export data. Defaults to the current user.
    :return: The exported template data as an in-memory byte stream using
        :class:`io.BytesIO` or ``None`` if an unknown export type was given.
    """
    export_filter = export_filter if export_filter is not None else {}
    user = user if user is not None else current_user

    if export_type == const.EXPORT_TYPE_JSON:
        return get_json_data(template, export_filter, user)

    if export_type == const.EXPORT_TYPE_JSON_SCHEMA:
        return get_json_schema_data(template, export_filter, user)

    if export_type == const.EXPORT_TYPE_SHACL:
        return get_shacl_data(template, export_filter, user)

    return None
