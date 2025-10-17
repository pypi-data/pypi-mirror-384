# Copyright 2025 Karlsruhe Institute of Technology
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
import re
from importlib import metadata

from flask import current_app
from marshmallow import fields

import kadi.lib.constants as const
from kadi.lib.schemas import CustomString
from kadi.lib.web import parse_url_rule


MODULE_REGEX = re.compile(r"kadi\.modules\.([a-z]+)[^\s]+")

MODULE_MAP = {
    "accounts": "users",
    "main": "misc",
}

PATH_TYPE_MAP = {
    "int": "integer",
}

SCHEMA_TYPE_MAP = {
    CustomString: "string",
    fields.String: "string",
    fields.Integer: "integer",
    fields.Boolean: "boolean",
}


class OpenAPISpec:
    """Container class for generating OpenAPI specification of Kadi4Mat's HTTP API.

    Uses OpenAPI specification version ``3.1.1``.

    :param version: The version of the Kadi4Mat HTTP API to generate the specification
        for. If the given version is invalid, the default API version as defined in
        :const:`kadi.lib.constants.API_VERSION_DEFAULT` is used.
    :param app: (optional) The application to generate the specification for. Defaults
        to the current application.
    """

    def __init__(self, version, app=None):
        self.version = (
            version if version in const.API_VERSIONS else const.API_VERSION_DEFAULT
        )
        self.app = app if app is not None else current_app

        kadi_version = metadata.version("kadi")

        self._routes = []
        self._spec = {
            "openapi": "3.1.1",
            "info": {
                "title": f"Kadi4Mat HTTP API {self.version}",
                "summary": (
                    f"The HTTP API {self.version} of the virtual research environment"
                    " Kadi4Mat."
                ),
                "description": (
                    f"This specification was generated using Kadi4Mat version"
                    f" `{kadi_version}` and documents all endpoints corresponding to"
                    f" Kadi4Mat's HTTP API version `{self.version}`.\n\nFor more"
                    " information about Kadi4Mat, please see its"
                    f" [website]({const.URL_INDEX})."
                ),
                "version": kadi_version,
            },
            "servers": [
                {"url": self.app.base_url},
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "description": "A personal access token or an OAuth2 token.",
                        "scheme": "bearer",
                    },
                },
            },
        }

        self._collect_routes()
        self._populate_paths()

    @property
    def spec(self):
        """Get the OpenAPI specification as a dictionary."""
        return self._spec

    def _collect_routes(self):
        for rule in self.app.url_map.iter_rules():
            endpoint = rule.endpoint
            view_func = self.app.view_functions[endpoint]

            # Exclude non-API endpoints and endpoints that don't match the given API
            # version.
            if not endpoint.startswith("api.") or not endpoint.endswith(
                f"_{self.version}"
            ):
                continue

            # Exclude internal and experimental endpoints.
            apispec_meta = getattr(view_func, const.APISPEC_META_ATTR, {})

            is_internal = apispec_meta.get(const.APISPEC_INTERNAL_KEY, False)
            is_experimental = apispec_meta.get(const.APISPEC_EXPERIMENTAL_KEY, False)

            if is_internal or is_experimental:
                continue

            # Exclude endpoints that are not part of a Kadi4Mat "module".
            match = MODULE_REGEX.search(view_func.__module__)

            if not match:
                continue

            module = match.group(1)
            module = MODULE_MAP.get(module, module)
            method = list(rule.methods.difference({"OPTIONS", "HEAD"}))[0].lower()

            route = {
                "endpoint": endpoint,
                "func": view_func,
                "method": method,
                "module": module,
                "parameters": {},
                "path": "",
            }

            for conv, _, var in parse_url_rule(rule.rule):
                if conv:
                    route["path"] += f"{{{var}}}"
                    route["parameters"][var] = conv
                else:
                    route["path"] += var

            self._routes.append(route)

        self._routes.sort(key=lambda route: route["path"])

    def _populate_paths(self):
        for route in self._routes:
            path = route["path"]
            view_func = route["func"]

            if path not in self.spec["paths"]:
                self.spec["paths"][path] = {}

            summary, description = self._extract_docstring(view_func)
            operation_spec = {
                "tags": [route["module"]],
                "summary": summary,
                "operationId": route["endpoint"],
                "responses": {},
            }

            if description:
                operation_spec["description"] = description

            apispec_meta = getattr(view_func, const.APISPEC_META_ATTR, {})

            self._add_security(operation_spec, apispec_meta)
            self._add_responses(operation_spec, apispec_meta)
            self._add_parameters(operation_spec, apispec_meta, route)
            self._add_request_body(operation_spec, apispec_meta, route)

            self.spec["paths"][path][route["method"]] = operation_spec

    def _extract_docstring(self, view_func):
        sections = view_func.__doc__.split("\n\n")

        summary = sections[0]
        description = ""

        if len(sections) > 1:
            for section in sections[1:]:
                lines = [line.strip() for line in section.splitlines()]
                description += f"{' '.join(lines)}\n\n"

            description = description.strip()

        return summary, self._prepare_description(description)

    def _prepare_description(self, description):
        # Replace textual references to other endpoints with the versioned endpoint.
        path_prefix = "/api/"
        description = description.replace(path_prefix, f"{path_prefix}{self.version}/")

        # Replace textual references to module functions with a corresponding
        # documentation hyperlink.
        def _replace_reference(match):
            ref = match.group(0)
            return f"[`{ref}()`]({const.URL_RTD_STABLE}/apiref/modules.html#{ref})"

        return MODULE_REGEX.sub(_replace_reference, description)

    def _add_security(self, operation_spec, apispec_meta):
        scopes = apispec_meta.get(const.APISPEC_SCOPES_KEY, [])
        operation_spec["security"] = [{"bearerAuth": scopes}]

    def _add_responses(self, operation_spec, apispec_meta):
        status_meta = apispec_meta.get(const.APISPEC_STATUS_KEY, {})

        for status_code, description in status_meta.items():
            operation_spec["responses"][status_code] = {
                "description": self._prepare_description(description)
            }

    def _add_parameters(self, operation_spec, apispec_meta, route):
        parameters = []

        # Add path parameters.
        for name, type in route["parameters"].items():
            parameters.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {
                        "type": PATH_TYPE_MAP.get(type, "string"),
                    },
                }
            )

        # Add header parameters.
        reqheaders_meta = apispec_meta.get(const.APISPEC_REQ_HEADERS_KEY, {})

        for name, data in reqheaders_meta.items():
            header_param = {
                "name": name,
                "in": "header",
                "description": self._prepare_description(data.get("description", "")),
                "schema": {
                    "type": data.get("type", "string"),
                },
            }

            if data.get("required", False):
                header_param["required"] = True

            parameters.append(header_param)

        # Add pagination query parameters.
        pagination_meta = apispec_meta.get(const.APISPEC_PAGINATION_KEY, {})

        if pagination_meta:
            page_param = {
                "name": "page",
                "in": "query",
                "description": "The current result page.",
                "schema": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1,
                },
            }

            page_max = pagination_meta["page_max"]

            if page_max:
                page_param["schema"]["maximum"] = page_max

            per_page_param = {
                "name": "per_page",
                "in": "query",
                "description": "Number of results per page.",
                "schema": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": pagination_meta["per_page_max"],
                },
            }

            parameters += [page_param, per_page_param]

        # Add all other query parameters.
        qparam_meta = apispec_meta.get(const.APISPEC_QPARAMS_KEY, {})

        for name, data in qparam_meta.items():
            qparam = {
                "name": name,
                "in": "query",
                "description": self._prepare_description(data["description"]),
                "schema": {
                    "type": data["type"],
                },
            }

            if data["multiple"]:
                qparam["schema"] = {
                    "type": "array",
                    "items": qparam["schema"],
                }

            if choice := data["choice"]:
                qparam["schema"]["enum"] = choice

            default_value = data["default"]

            if default_value is not None and default_value != "":
                if not isinstance(default_value, (str, int, bool)):
                    default_value = str(default_value)

                qparam["schema"]["default"] = default_value

            parameters.append(qparam)

        if parameters:
            operation_spec["parameters"] = parameters

    def _add_request_body(self, operation_spec, apispec_meta, route):
        reqschema_meta = apispec_meta.get(const.APISPEC_REQ_SCHEMA_KEY, {})

        if reqschema_meta:
            fields = self._get_schema_fields(reqschema_meta["schema"])
            schema = self._get_request_schema(fields)

            operation_spec["requestBody"] = {
                "required": True,
                "description": self._prepare_description(reqschema_meta["description"]),
                "content": {
                    const.MIMETYPE_JSON: {"schema": schema},
                },
            }
        elif route["method"] == "put":
            # We just assume that a binary upload is required in this case, as there is
            # currently no other way to retrieve this information.
            operation_spec["requestBody"] = {
                "required": True,
                "content": {const.MIMETYPE_BINARY: {}},
            }

    def _get_schema_fields(self, schema, is_partial=False):
        def _get_field_attr(field, attr, default=None):
            # Try to retrieve the attribute from the custom field metadata first.
            if attr in field.metadata:
                return field.metadata[attr]

            if hasattr(field, attr):
                return getattr(field, attr)

            return default

        schema_fields = {}

        for name, field in schema.fields.items():
            if field.dump_only:
                continue

            field_meta = {
                "required": _get_field_attr(field, "required", False),
                "many": _get_field_attr(field, "many", False),
                "type": _get_field_attr(
                    field, "type", SCHEMA_TYPE_MAP.get(field.__class__, "object")
                ),
            }

            is_partial = is_partial or (
                schema.partial is True
                or (isinstance(schema.partial, tuple) and name in schema.partial)
            )

            if is_partial:
                field_meta["required"] = False

            if isinstance(field, fields.Pluck):
                field_meta["type"] = SCHEMA_TYPE_MAP.get(
                    field.schema.fields[field.field_name].__class__, "object"
                )
            elif isinstance(field, fields.Nested):
                # Pass along the information whether the schema is loaded partially, as
                # we can't retrieve it from the nested schema directly.
                field_meta["nested"] = self._get_schema_fields(
                    field.schema, is_partial=is_partial
                )

            schema_fields[name] = field_meta

        sorted_fields = sorted(schema_fields.items(), key=lambda field: field[0])
        sorted_fields = sorted(
            sorted_fields, key=lambda field: field[1]["required"], reverse=True
        )

        return dict(sorted_fields)

    def _get_request_schema(self, fields):
        properties = {}
        required_fields = []

        for name, data in fields.items():
            # If the type definition has been provided as a dictionary, take it as-is.
            if isinstance(data["type"], dict):
                properties[name] = data["type"]
            else:
                if "nested" in data:
                    properties[name] = self._get_request_schema(data["nested"])
                else:
                    properties[name] = {"type": data["type"]}

                if data["many"]:
                    properties[name] = {
                        "type": "array",
                        "items": {"type": properties[name]["type"]},
                    }

            if data["required"]:
                required_fields.append(name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required_fields:
            schema["required"] = required_fields

        return schema
