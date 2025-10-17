# Copyright 2020 Karlsruhe Institute of Technology
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
from flask_babel import lazy_gettext as _l


# Amount of bytes (decimal interpretation).
ONE_KB = 1_000
ONE_MB = 1_000 * ONE_KB
ONE_GB = 1_000 * ONE_MB
ONE_TB = 1_000 * ONE_GB

# Amount of bytes (binary interpretation).
ONE_KIB = 1_024
ONE_MIB = 1_024 * ONE_KIB
ONE_GIB = 1_024 * ONE_MIB
ONE_TIB = 1_024 * ONE_GIB

# Amount of seconds.
ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = 24 * ONE_HOUR
ONE_WEEK = 7 * ONE_DAY


# Default MIME type for unspecified binary files.
MIMETYPE_BINARY = "application/octet-stream"

# Preferred MIME type for CSV files.
MIMETYPE_CSV = "text/csv"
# Preferred MIME type for JSON files.
MIMETYPE_JSON = "application/json"
# Preferred MIME type for XML files.
MIMETYPE_XML = "application/xml"

# Custom MIME type for dashboard files.
MIMETYPE_DASHBOARD = "application/x-dashboard+json"
# Custom MIME type for flow files to define workflows.
MIMETYPE_FLOW = "application/x-flow+json"
# Custom MIME type for tool files to be used within workflows.
MIMETYPE_TOOL = "application/x-tool+xml"

# Various other commonly used MIME types.
MIMETYPE_FORMDATA = "multipart/form-data"
MIMETYPE_HTML = "text/html"
MIMETYPE_JPEG = "image/jpeg"
MIMETYPE_JSONLD = "application/ld+json"
MIMETYPE_MD = "text/markdown"
MIMETYPE_PDF = "application/pdf"
MIMETYPE_PNG = "image/png"
MIMETYPE_TEXT = "text/plain"
MIMETYPE_TTL = "text/turtle"
MIMETYPE_ZIP = "application/zip"


# Amount of seconds specifying the minimum interval to update the last usage date of
# access tokens.
ACCESS_TOKEN_LAST_USED_INTERVAL = 10

# All additional access token scopes that are not tied to any resource permissions.
ACCESS_TOKEN_SCOPES = {
    "user": ["read"],
    "misc": ["manage_trash"],
}

# All available prefixes to distinguish different types of access tokens.
ACCESS_TOKEN_PREFIX_OAUTH = "oat_"
ACCESS_TOKEN_PREFIX_PAT = "pat_"


# Maximum time in seconds after which active uploads are cleaned up.
ACTIVE_UPLOADS_MAX_AGE = ONE_DAY


# All API versions that are currently available.
API_VERSIONS = ["v1"]

# The default API version to use when no version is specified in a request, which
# corresponds to the latest stable version.
API_VERSION_DEFAULT = "v1"


# Name of the attribute to store the API specification meta dictionary within view
# functions.
APISPEC_META_ATTR = "__apispec__"

# Keys to store various information in the API specification meta dictionary.
APISPEC_EXPERIMENTAL_KEY = "experimental"
APISPEC_INTERNAL_KEY = "internal"
APISPEC_PAGINATION_KEY = "pagination"
APISPEC_QPARAMS_KEY = "qparams"
APISPEC_REQ_HEADERS_KEY = "reqheaders"
APISPEC_REQ_SCHEMA_KEY = "reqschema"
APISPEC_SCOPES_KEY = "scopes"
APISPEC_STATUS_KEY = "status"


# Type values for all built-in authentication providers and identities.
AUTH_PROVIDER_TYPE_LDAP = "ldap"
AUTH_PROVIDER_TYPE_LOCAL = "local"
AUTH_PROVIDER_TYPE_OIDC = "oidc"
AUTH_PROVIDER_TYPE_SHIB = "shib"

# All currently available built-in authentication providers and their corresponding
# provider, identity and form classes.
AUTH_PROVIDER_TYPES = {
    AUTH_PROVIDER_TYPE_LOCAL: {
        "provider": "kadi.modules.accounts.providers.LocalProvider",
        "identity": "kadi.modules.accounts.models.LocalIdentity",
        "form": "kadi.modules.accounts.forms.CredentialsLoginForm",
    },
    AUTH_PROVIDER_TYPE_LDAP: {
        "provider": "kadi.modules.accounts.providers.LDAPProvider",
        "identity": "kadi.modules.accounts.models.LDAPIdentity",
        "form": "kadi.modules.accounts.forms.CredentialsLoginForm",
    },
    AUTH_PROVIDER_TYPE_OIDC: {
        "provider": "kadi.modules.accounts.providers.OIDCProvider",
        "identity": "kadi.modules.accounts.models.OIDCIdentity",
        "form": "kadi.modules.accounts.forms.OIDCLoginForm",
    },
    AUTH_PROVIDER_TYPE_SHIB: {
        "provider": "kadi.modules.accounts.providers.ShibProvider",
        "identity": "kadi.modules.accounts.models.ShibIdentity",
        "form": "kadi.modules.accounts.forms.ShibLoginForm",
    },
}


# Capability to define support for searching metadata terms in a terminology service.
CAPABILITY_TERM_SEARCH = "term_search"


# Maximum time in seconds after which deleted resources are cleaned up.
DELETED_RESOURCES_MAX_AGE = ONE_WEEK


# Values for the possible Kadi environments.
ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"
ENV_TESTING = "testing"


# Common user attributes that are excluded in all resource and export types where they
# are relevant.
EXPORT_EXCLUDE_USER_ATTRS = [
    "creator.state",
    "creator.identity",
    "creator.created_at",
    "creator.is_sysadmin",
    "creator.system_role",
    "creator._links",
    "creator._actions",
]

# All currently available export types.
EXPORT_TYPE_JSON = "json"
EXPORT_TYPE_JSON_SCHEMA = "json-schema"
EXPORT_TYPE_PDF = "pdf"
EXPORT_TYPE_QR = "qr"
EXPORT_TYPE_RDF = "rdf"
EXPORT_TYPE_RO_CRATE = "ro-crate"
EXPORT_TYPE_SHACL = "shacl"

# Mapping of different resource types to their supported export types and corresponding
# metadata.
EXPORT_TYPES = {
    "record": {
        EXPORT_TYPE_JSON: {"title": "JSON", "ext": "json"},
        EXPORT_TYPE_RDF: {"title": "RDF (Turtle)", "ext": "ttl"},
        EXPORT_TYPE_PDF: {"title": "PDF", "ext": "pdf"},
        EXPORT_TYPE_QR: {"title": "QR Code", "ext": "png"},
        EXPORT_TYPE_RO_CRATE: {"title": "RO-Crate", "ext": "eln"},
    },
    "extras": {
        EXPORT_TYPE_JSON: {"title": "JSON", "ext": "json"},
    },
    "collection": {
        EXPORT_TYPE_JSON: {"title": "JSON", "ext": "json"},
        EXPORT_TYPE_RDF: {"title": "RDF (Turtle)", "ext": "ttl"},
        EXPORT_TYPE_QR: {"title": "QR Code", "ext": "png"},
        EXPORT_TYPE_RO_CRATE: {"title": "RO-Crate", "ext": "eln"},
    },
    "template": {
        EXPORT_TYPE_JSON: {"title": "JSON", "ext": "json"},
        EXPORT_TYPE_JSON_SCHEMA: {"title": "JSON Schema", "ext": "json"},
        EXPORT_TYPE_SHACL: {"title": "SHACL (Turtle)", "ext": "ttl"},
    },
}


# Maximum and minimum values for integers in the extra metadata. This way, the values
# are always safe for using them in JS contexts, where all numbers are 64 bit floating
# point numbers. This should probably be enough for most use cases, and as a positive
# side effect, all integer values are indexable by Elasticsearch.
EXTRAS_MAX_INTEGER = 2**53 - 1
EXTRAS_MIN_INTEGER = -EXTRAS_MAX_INTEGER


# Maximum time in seconds after which finished tasks are cleaned up.
FINISHED_TASKS_MAX_AGE = ONE_WEEK


# Maximum size in bytes for image uploads used for generating image thumbnails.
IMAGE_MAX_SIZE = 10 * ONE_MB

# Supported MIME types for image uploads and direct image previews.
IMAGE_MIMETYPES = [MIMETYPE_JPEG, MIMETYPE_PNG]


# Maximum size in bytes for file imports.
IMPORT_MAX_SIZE = 10 * ONE_MB

# All currently available import types.
IMPORT_TYPE_JSON = "json"
IMPORT_TYPE_JSON_SCHEMA = "json-schema"
IMPORT_TYPE_SHACL = "shacl"


# Maximum time in seconds after which inactive files are cleaned up.
INACTIVE_FILES_MAX_AGE = ONE_DAY

# Maximum time in seconds after which inactive uploads are cleaned up.
INACTIVE_UPLOADS_MAX_AGE = 5 * ONE_MINUTE


# Time in seconds after which JWTs sent via email expire.
JWT_MAIL_EXPIRES_IN = 10 * ONE_MINUTE

# Type values for different kinds of JWTs.
JWT_TYPE_EMAIL_CONFIRMATION = "email_confirmation"
JWT_TYPE_PASSWORD_RESET = "password_reset"


# All locales that are currently available with corresponding titles.
LOCALES = {
    "en": "English",
    "de": "Deutsch",
}

# Name of the locale cookie.
LOCALE_COOKIE_NAME = "locale"

# The default locale.
LOCALE_DEFAULT = "en"


# Active state value for all stateful models.
MODEL_STATE_ACTIVE = "active"
# Deleted state value for all stateful models. For the main resource types, this is used
# to represent soft deletion, but may have different semantics in other cases.
MODEL_STATE_DELETED = "deleted"


# Time in seconds after which OAuth2 authorization codes expire.
OAUTH_AUTH_CODE_EXPIRES_IN = 5 * ONE_MINUTE

# All currently registered OAuth2 grant types.
OAUTH_GRANT_AUTH_CODE = "authorization_code"
OAUTH_GRANT_REFRESH_TOKEN = "refresh_token"

# The single response type to allow for OAuth2 clients to request.
OAUTH_RESPONSE_TYPE = "code"

# The single method to allow for OAuth2 client authentication when requesting a token.
OAUTH_TOKEN_ENDPOINT_AUTH_METHOD = "client_secret_post"

# The single OAuth2 token type that is currently used.
OAUTH_TOKEN_TYPE = "Bearer"


# Name of the plugin entry point.
PLUGIN_ENTRYPOINT = "kadi_plugins"


# Maximum size for file previews which require either the client or Kadi to (down)load
# the entire file. May be bypassed by the client on demand for some preview types.
PREVIEW_MAX_SIZE = 25 * ONE_MB


# All currently available types for query parameters.
QPARAM_TYPE_BOOL = "boolean"
QPARAM_TYPE_INT = "integer"
QPARAM_TYPE_STR = "string"


# Maximum length of all resource descriptions.
RESOURCE_DESCRIPTION_MAX_LEN = 50_000

# Maximum length of all resource identifiers.
RESOURCE_IDENTIFIER_MAX_LEN = 50

# Maximum length of all resource titles.
RESOURCE_TITLE_MAX_LEN = 150


# All currently available main resource types and their corresponding model class,
# schema class and other attributes.
RESOURCE_TYPES = {
    "record": {
        "model": "kadi.modules.records.models.Record",
        "schema": "kadi.modules.records.schemas.RecordSchema",
        "title": _l("Record"),
        "title_plural": _l("Records"),
        "endpoint": "records.records",
    },
    "collection": {
        "model": "kadi.modules.collections.models.Collection",
        "schema": "kadi.modules.collections.schemas.CollectionSchema",
        "title": _l("Collection"),
        "title_plural": _l("Collections"),
        "endpoint": "collections.collections",
    },
    "template": {
        "model": "kadi.modules.templates.models.Template",
        "schema": "kadi.modules.templates.schemas.TemplateSchema",
        "title": _l("Template"),
        "title_plural": _l("Templates"),
        "endpoint": "templates.templates",
    },
    "group": {
        "model": "kadi.modules.groups.models.Group",
        "schema": "kadi.modules.groups.schemas.GroupSchema",
        "title": _l("Group"),
        "title_plural": _l("Groups"),
        "endpoint": "groups.groups",
    },
}

# Private visibility value for all resources.
RESOURCE_VISIBILITY_PRIVATE = "private"
# Public visibility value for all resources.
RESOURCE_VISIBILITY_PUBLIC = "public"


# Keys for storing custom values in the Flask session cookie.
SESSION_KEY_COLLECTION_CONTEXT = "collection_context"
SESSION_KEY_NEXT_URL = "next_url"
SESSION_KEY_OIDC_DATA = "oidc_data"


# Storage type of the built-in local storage provider.
STORAGE_TYPE_LOCAL = "local"


# Keys for global config items.
SYS_CONFIG_BROADCAST_MESSAGE = "BROADCAST_MESSAGE"
SYS_CONFIG_BROADCAST_MESSAGE_PUBLIC = "BROADCAST_MESSAGE_PUBLIC"
SYS_CONFIG_NAV_FOOTER_ITEMS = "NAV_FOOTER_ITEMS"
SYS_CONFIG_INDEX_IMAGE = "INDEX_IMAGE"
SYS_CONFIG_INDEX_TEXT = "INDEX_TEXT"

SYS_CONFIG_TERMS_OF_USE = "TERMS_OF_USE"
SYS_CONFIG_PRIVACY_POLICY = "PRIVACY_POLICY"
SYS_CONFIG_ENFORCE_LEGALS = "ENFORCE_LEGALS"
SYS_CONFIG_LEGAL_NOTICE = "LEGAL_NOTICE"

SYS_CONFIG_ROBOTS_NOINDEX = "ROBOTS_NOINDEX"


# All currently available system roles that group global actions of different resources.
SYSTEM_ROLES = {
    "admin": {
        "record": ["create", "read", "update", "link", "permissions", "delete"],
        "collection": ["create", "read", "update", "link", "permissions", "delete"],
        "template": ["create", "read", "update", "permissions", "delete"],
        "group": ["create", "read", "update", "members", "delete"],
    },
    "member": {
        "record": ["create"],
        "collection": ["create"],
        "template": ["create"],
        "group": ["create"],
    },
    "guest": {},
}


# Names of all currently available Celery tasks.
TASK_APPLY_ROLE_RULES = "kadi.permissions.apply_role_rules"
TASK_MERGE_CHUNKS = "kadi.records.merge_chunks"
TASK_MERGE_USERS = "kadi.accounts.merge_users"
TASK_PERIODIC_CLEANUP = "kadi.main.periodic_cleanup"
TASK_PUBLISH_RESOURCE = "kadi.resources.publish_resource"
TASK_PURGE_RECORD = "kadi.records.purge_record"
TASK_PURGE_RESOURCES = "kadi.resources.purge_resources"
TASK_SEND_MAIL = "kadi.notifications.send_mail"


# The size of each chunk for chunked uploads, only the final chunk may be smaller.
UPLOAD_CHUNK_SIZE = 10 * ONE_MB

# The maximum size for direct uploads.
UPLOAD_CHUNKED_BOUNDARY = 50 * ONE_MB


# URL of the AIMS Project.
URL_AIMS = "https://www.aims-projekt.de"

# URL of the ELN file format specification.
URL_ELN_SPEC = "http://purl.org/elnconsortium/eln-spec"

# URL of the Kadi landing/index page.
URL_INDEX = "https://kadi.iam.kit.edu"

# URL of ORCID.
URL_ORCID = "https://orcid.org"

# URL from which the latest released Kadi version is retrieved.
URL_PYPI = "https://pypi.org/pypi/kadi/json"

# URLs where the documentation is hosted.
URL_RTD_STABLE = "https://kadi.readthedocs.io/en/stable"
URL_RTD_LATEST = "https://kadi.readthedocs.io/en/latest"


# Keys for user-specific config items.
USER_CONFIG_EXTRAS_EDITING_MODE = "EXTRAS_EDITING_MODE"
USER_CONFIG_HIDE_INTRODUCTION = "HIDE_INTRODUCTION"
USER_CONFIG_HOME_LAYOUT = "HOME_LAYOUT"

# Default values for user-specific config items.
USER_CONFIG_HOME_LAYOUT_DEFAULT = [
    {
        "resource": "record",
        "max_items": 6,
        "creator": "any",
        "visibility": "all",
        "explicit_permissions": False,
    },
    {
        "resource": "collection",
        "max_items": 4,
        "creator": "any",
        "visibility": "all",
        "explicit_permissions": False,
    },
]


# Environment variables defined and used within Kadi.
VAR_API_BP = "KADI_IGNORE_API_BP_SETUP_CHECK"
VAR_CLI = "KADI_APP_FROM_CLI"
VAR_CONFIG = "KADI_CONFIG_FILE"
VAR_ENV = "KADI_ENV"
