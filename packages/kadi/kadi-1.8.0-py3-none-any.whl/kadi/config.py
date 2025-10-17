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
import os
import socket

import kadi.lib.constants as const


class BaseConfig:
    """Base configuration."""

    ###########
    # Authlib #
    ###########

    OAUTH2_ACCESS_TOKEN_GENERATOR = "kadi.lib.oauth.utils.new_oauth2_access_token"

    OAUTH2_REFRESH_TOKEN_GENERATOR = "kadi.lib.oauth.utils.new_oauth2_refresh_token"

    OAUTH2_TOKEN_EXPIRES_IN = {
        const.OAUTH_GRANT_AUTH_CODE: const.ONE_HOUR,
    }

    OIDC_ID_TOKEN_EXPIRES_IN = const.ONE_HOUR

    OIDC_SIGNING_KEYS = []

    ##########
    # Celery #
    ##########

    # Will default to "True" in a future release.
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

    # So we don't retry forever if the broker is not reachable.
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    }

    CELERY_BROKER_URL = "redis://localhost:6379/0"

    # Will default to "True" in a future release.
    CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True

    # Use a maximum of 10 worker processes, also to limit the amount of database
    # connections.
    CELERY_WORKER_CONCURRENCY = min(os.cpu_count() or 4, 10)

    CELERY_WORKER_REDIRECT_STDOUTS = False

    #########
    # Flask #
    #########

    SESSION_COOKIE_NAME = "kadi_session"

    ###############
    # Flask-Babel #
    ###############

    BABEL_DEFAULT_LOCALE = const.LOCALE_DEFAULT

    #################
    # Flask-Limiter #
    #################

    RATELIMIT_STORAGE_URI = "redis://localhost:6379/0"

    ###############
    # Flask-Login #
    ###############

    # Makes a stolen cookie much harder to use by using a session identifier.
    SESSION_PROTECTION = "strong"

    ####################
    # Flask-SQLAlchemy #
    ####################

    SQLALCHEMY_DATABASE_URI = None

    # To enable pessimistic disconnect handling.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    #################
    # Flask-WTForms #
    #################

    WTF_CSRF_TIME_LIMIT = None

    ########
    # Kadi #
    ########

    AUTH_PROVIDERS = [{"type": const.AUTH_PROVIDER_TYPE_LOCAL}]

    BACKEND_TRANSLATIONS_PATH = os.path.join("{root_path}", "translations")

    BROADCAST_MESSAGE = ""

    BROADCAST_MESSAGE_PUBLIC = False

    CAPABILITIES = set()

    ENFORCE_LEGALS = False

    EXPERIMENTAL_FEATURES = False

    FEDERATED_INSTANCES = {}

    # Path for fonts used outside the web browser context.
    FONTS_PATH = os.path.join("{root_path}", "assets", "fonts")

    INDEX_IMAGE = None

    INDEX_TEXT = ""

    LEGAL_NOTICE = ""

    LOCALE_COOKIE_SECURE = False

    MAIL_ERROR_LOGS = []

    MAIL_NO_REPLY = f"no-reply@{socket.getfqdn()}"

    MAIL_SUBJECT_HEADER = "Kadi4Mat"

    MANIFEST_MAPPING = {}

    MANIFEST_PATH = os.path.join("{static_path}", "manifest.json")

    MIGRATIONS_PATH = os.path.join("{root_path}", "migrations")

    MISC_UPLOADS_PATH = None

    NAV_FOOTER_ITEMS = []

    PLUGIN_CONFIG = {}

    PLUGINS = []

    PRIVACY_POLICY = ""

    PROXY_FIX_HEADERS = None

    RATELIMIT_ANONYMOUS_USER = "90/minute;3/second"

    RATELIMIT_AUTHENTICATED_USER = ""

    RATELIMIT_IP_WHITELIST = ["127.0.0.1"]

    # Path for miscellaneous resources used outside the web browser context.
    RESOURCES_PATH = os.path.join("{root_path}", "assets", "resources")

    ROBOTS_NOINDEX = False

    SENTRY_DSN = None

    SMTP_HOST = "localhost"

    SMTP_PASSWORD = ""

    SMTP_PORT = 25

    SMTP_TIMEOUT = 60

    SMTP_USE_TLS = False

    SMTP_USERNAME = ""

    STORAGE_PATH = None

    STORAGE_PROVIDER = const.STORAGE_TYPE_LOCAL

    TERMS_OF_USE = ""

    UPLOAD_USER_QUOTA = 10 * const.ONE_GB

    WORKFLOW_FEATURES = False


class ProductionConfig(BaseConfig):
    """Production configuration."""

    #########
    # Flask #
    #########

    PREFERRED_URL_SCHEME = "https"

    SESSION_COOKIE_SECURE = True

    USE_X_SENDFILE = True

    ########
    # Kadi #
    ########

    LOCALE_COOKIE_SECURE = True

    SMTP_USE_TLS = True


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    #################
    # Elasticsearch #
    #################

    # Ignore Elasticsearch not running and use a basic search fallback.
    ELASTICSEARCH_ENABLE_FALLBACK = True

    #########
    # Flask #
    #########

    SECRET_KEY = "s3cr3t"

    SERVER_NAME = "localhost:5000"

    ####################
    # Flask-SQLAlchemy #
    ####################

    SQLALCHEMY_DATABASE_URI = "postgresql://kadi:kadi@localhost/kadi"

    ########
    # Kadi #
    ########

    AUTH_PROVIDERS = [
        {"type": const.AUTH_PROVIDER_TYPE_LOCAL, "allow_registration": True}
    ]

    EXPERIMENTAL_FEATURES = True

    MISC_UPLOADS_PATH = os.path.join("{instance_path}", "uploads")

    SMTP_PORT = 8_025

    STORAGE_PATH = os.path.join("{instance_path}", "storage")


class TestingConfig(BaseConfig):
    """Testing configuration."""

    ##########
    # Celery #
    ##########

    # Ensure Celery is never used.
    CELERY_BROKER_URL = None

    #################
    # Elasticsearch #
    #################

    # Ensure Elasticsearch is never used.
    ELASTICSEARCH_HOSTS = None

    #########
    # Flask #
    #########

    SECRET_KEY = "s3cr3t"

    SERVER_NAME = "localhost"

    TESTING = True

    #################
    # Flask-Limiter #
    #################

    RATELIMIT_STORAGE_URI = "memory://"

    ####################
    # Flask-SQLAlchemy #
    ####################

    SQLALCHEMY_DATABASE_URI = "postgresql://kadi_test:kadi_test@localhost/kadi_test"

    #################
    # Flask-WTForms #
    #################

    WTF_CSRF_ENABLED = False

    ########
    # Kadi #
    ########

    AUTH_PROVIDERS = [
        {
            "type": const.AUTH_PROVIDER_TYPE_LOCAL,
            "allow_registration": True,
        },
        {
            "type": const.AUTH_PROVIDER_TYPE_LDAP,
        },
        {
            "type": const.AUTH_PROVIDER_TYPE_OIDC,
            "providers": [{"name": "test"}],
        },
        {
            "type": const.AUTH_PROVIDER_TYPE_SHIB,
            "idps": [{"entity_id": "https://idp.example.com"}],
        },
    ]

    EXPERIMENTAL_FEATURES = True

    FEDERATED_INSTANCES = {
        "test": {
            "url": "https://example.com",
            "client_id": "foo",
            "client_secret": "bar",
        }
    }

    PLUGIN_CONFIG = {
        "influxdb": {
            "test": {
                "url": "https://foo.bar",
            }
        },
        "zenodo": {
            "base_url": "https://foo.bar",
            "client_id": "foo",
            "client_secret": "bar",
        },
    }

    PLUGINS = ["influxdb", "zenodo"]


CONFIG_CLASSES = {
    const.ENV_PRODUCTION: ProductionConfig,
    const.ENV_DEVELOPMENT: DevelopmentConfig,
    const.ENV_TESTING: TestingConfig,
}
