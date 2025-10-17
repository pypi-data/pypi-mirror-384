# Copyright 2024 Karlsruhe Institute of Technology
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
from io import BytesIO

import jsonref
from flask import current_app
from flask import json
from rdflib import DCTERMS
from rdflib import RDF
from rdflib import SH
from rdflib import XSD
from rdflib import Graph
from rdflib.collection import Collection as RDFCollection

import kadi.lib.constants as const
from kadi.modules.records.extras import remove_extra_values
from kadi.modules.records.schemas import RecordImportSchema

from .models import TemplateType
from .schemas import TemplateImportSchema


JSON_SCHEMA_TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}

XSD_TYPE_MAPPING = {
    XSD.string: "str",
    XSD.integer: "int",
    XSD.int: "int",
    XSD.float: "float",
    XSD.decimal: "float",
    XSD.double: "float",
    XSD.boolean: "bool",
    XSD.dateTime: "date",
}


def _parse_json_data(import_data, template_type):
    try:
        import_data = json.load(import_data)

        if not isinstance(import_data, dict):
            return None

        # Basic check if we are dealing with template data. We assume record data
        # otherwise.
        if "data" in import_data:
            import_template_type = import_data.get("type")
            import_data = TemplateImportSchema(
                template_type=import_template_type, partial=True
            ).load(import_data)
        else:
            import_template_type = TemplateType.RECORD
            import_data = RecordImportSchema(partial=True).load(import_data)

            # Remove the values of extras when dealing with record data.
            if "extras" in import_data:
                import_data["extras"] = remove_extra_values(import_data["extras"])

            import_data = {"data": import_data}

        # Allow using record data for extras templates and vice versa.
        if (
            template_type == TemplateType.RECORD
            and import_template_type == TemplateType.EXTRAS
        ):
            import_data["data"] = {"extras": import_data.get("data", [])}

        elif (
            template_type == TemplateType.EXTRAS
            and import_template_type == TemplateType.RECORD
        ):
            import_data["data"] = import_data.get("data", {}).get("extras", [])

        elif template_type != import_template_type:
            return None

        return import_data

    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        return None


def _ordered_properties(properties, properties_order):
    if not properties_order:
        return properties.items()

    def _order_func(item):
        try:
            return properties_order.index(item[0])
        except ValueError:
            return 0

    return sorted(properties.items(), key=_order_func)


def _json_schema_to_extras(properties, properties_order=None, required_props=None):
    required_props = required_props if required_props is not None else []
    properties_order = properties_order if properties_order is not None else []

    extras = []

    if isinstance(properties, dict):
        properties_iter = _ordered_properties(properties, properties_order)
    else:
        properties_iter = enumerate(properties)

    for key, value in properties_iter:
        # Keys within lists will simply be ignored by the extra schema.
        extra = {"key": key}

        if (extra_description := value.get("description")) is not None:
            extra["description"] = str(extra_description)

        # We just use "string" as fallback type, as extras always need an explicit type.
        value_type = value.get("type", "string")

        if isinstance(value_type, list):
            value_type = value_type[0]

        if value_type in {"object", "array"}:
            extra["type"] = "dict" if value_type == "object" else "list"

            if value_type == "object":
                result = _json_schema_to_extras(
                    value.get("properties", {}),
                    value.get("propertiesOrder", []),
                    value.get("required", []),
                )
            else:
                if (items := value.get("items")) is not None:
                    result = _json_schema_to_extras([items])
                else:
                    result = _json_schema_to_extras(value.get("prefixItems", []))

            extra["value"] = result
        else:
            if value_type == "string":
                extra["type"] = "date" if value.get("format") == "date-time" else "str"
            else:
                extra["type"] = JSON_SCHEMA_TYPE_MAPPING.get(value_type, "str")

            if (default := value.get("default")) is not None:
                extra["value"] = default

            # This handling of the custom "unit" property only works for files exported
            # via Kadi.
            if (unit := value.get("unit")) is not None:
                extra["unit"] = unit.get("default")

            validation = {}

            if key in required_props:
                validation["required"] = True

            if (options := value.get("enum")) is not None:
                validation["options"] = options

            minimum = value.get("minimum")
            maximum = value.get("maximum")

            if minimum is not None or maximum is not None:
                validation["range"] = {"min": minimum, "max": maximum}

            if validation:
                extra["validation"] = validation

        extras.append(extra)

    return extras


def _parse_json_schema_data(import_data, template_type):
    try:
        import_data = jsonref.load(import_data)

        if not isinstance(import_data, dict):
            return None

        extras = _json_schema_to_extras(
            import_data.get("properties", {}),
            import_data.get("propertiesOrder", []),
            import_data.get("required", []),
        )

        if template_type == TemplateType.RECORD:
            import_data = {"data": {"extras": extras}}
        elif template_type == TemplateType.EXTRAS:
            import_data = {"data": extras}
        else:
            return None

        return TemplateImportSchema(template_type=template_type, partial=True).load(
            import_data
        )

    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        return None


def _ordered_objects(graph, subject, predicate):
    def _order_func(obj):
        order = graph.value(obj, SH.order)
        return order.value if order is not None else 0

    return sorted(graph.objects(subject, predicate), key=_order_func)


def _shacl_to_extras(graph, current_subject, visited=None):
    extras = []

    if visited is None:
        # Keep track of visited nodes to avoid potential loops, depending on the SHACL
        # structure.
        visited = set()

    # Handle (nested) objects that are referenced via sh:node.
    for node_objects in _ordered_objects(graph, current_subject, SH.node):
        extras.extend(_shacl_to_extras(graph, node_objects))

    # Handle objects that are referenced via sh:property.
    for property_object in _ordered_objects(graph, current_subject, SH.property):
        if (extra_key := graph.value(property_object, SH.name)) is None:
            continue

        extra = {
            # Keys within lists will simply be ignored by the extra schema.
            "key": extra_key.value,
            "type": "str",
            "value": None,
        }

        if (term_iri := graph.value(property_object, SH.path)) is not None:
            extra["term"] = str(term_iri)

        if (
            extra_description := graph.value(property_object, SH.description)
        ) is not None:
            extra["description"] = str(extra_description)

        # Handle nested objects that are referenced via sh:qualifiedValueShape or
        # sh:node.
        nested_objects = _ordered_objects(
            graph, property_object, SH.qualifiedValueShape
        ) or _ordered_objects(graph, property_object, SH.node)

        for nested_object in nested_objects:
            if nested_object is not None and nested_object not in visited:
                visited.add(nested_object)
                nested_extras = _shacl_to_extras(graph, nested_object, visited)

                # Use a list if the first key looks like an index, which is mostly
                # relevant for SHACL data exported via Kadi.
                if len(nested_extras) > 0 and nested_extras[0]["key"] == "0":
                    extra["type"] = "list"
                else:
                    extra["type"] = "dict"

                extra["value"] = nested_extras

        # Handle the individual extra objects.
        if (value_type := graph.value(property_object, SH.datatype)) is not None:
            # We use "str" as fallback type, as extras always need an explicit type.
            extra["type"] = XSD_TYPE_MAPPING.get(value_type, "str")

            if (
                default_value := graph.value(property_object, SH.defaultValue)
            ) is not None:
                extra["value"] = default_value.value

            validation = {}

            if value_type == XSD.anyURI:
                validation["iri"] = True

            if (
                min_count := graph.value(property_object, SH.minCount)
            ) is not None and min_count.value >= 1:
                validation["required"] = True

            if (options := graph.value(property_object, SH["in"])) is not None:
                options_list = RDFCollection(graph, options)
                validation["options"] = [option.value for option in options_list]

            minimum = graph.value(property_object, SH.minInclusive)
            maximum = graph.value(property_object, SH.maxInclusive)

            if minimum is not None or maximum is not None:
                validation["range"] = {
                    "min": minimum.value if minimum is not None else None,
                    "max": maximum.value if maximum is not None else None,
                }

            if validation:
                extra["validation"] = validation

        extras.append(extra)

    return extras


def _parse_shacl_data(import_data, template_type):
    try:
        graph = Graph()
        graph.parse(import_data, format="turtle")

        if (
            # This assumes that the "root" subject is always listed first.
            root_subject := graph.value(predicate=RDF.type, object=SH.NodeShape)
        ) is None:
            return None

        import_data = {}

        if (title := graph.value(root_subject, DCTERMS.title)) is not None:
            import_data["title"] = str(title)

        if (description := graph.value(root_subject, DCTERMS.description)) is not None:
            import_data["description"] = str(description)

        extras = _shacl_to_extras(graph, root_subject)

        if template_type == TemplateType.RECORD:
            import_data["data"] = {"extras": extras}
        elif template_type == TemplateType.EXTRAS:
            import_data["data"] = extras
        else:
            return None

        return TemplateImportSchema(template_type=template_type, partial=True).load(
            import_data
        )

    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        return None


def parse_import_data(stream, import_type, template_type):
    """Parse imported template data of a given format.

    :param stream: The import data as a readable binary stream.
    :param import_type: The import type, one of ``"json"``, ``"json-schema"`` or
        ``"shacl"``.
    :param template_type: The expected template type corresponding to the import data.
    :return: The imported template data as a dictionary or ``None`` if the data could
        not be parsed. Note that none of the template properties are guaranteed to be
        present.
    """
    import_data = BytesIO(stream.read(const.IMPORT_MAX_SIZE))

    if import_type == const.IMPORT_TYPE_JSON:
        return _parse_json_data(import_data, template_type)

    if import_type == const.IMPORT_TYPE_JSON_SCHEMA:
        return _parse_json_schema_data(import_data, template_type)

    if import_type == const.IMPORT_TYPE_SHACL:
        return _parse_shacl_data(import_data, template_type)

    return None
