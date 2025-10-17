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
import logging
import math
import os
import time
from functools import partial
from importlib import metadata
from logging.handlers import SMTPHandler
from tempfile import SpooledTemporaryFile

import sentry_sdk
from flask import Flask
from flask import Request
from flask import current_app
from flask import json
from flask import redirect
from flask import request
from flask import session
from flask.logging import default_handler
from flask_babel import format_number
from flask_babel import gettext as _
from flask_limiter.errors import RateLimitExceeded
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from pluggy import PluginManager
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

import kadi.lib.constants as const
from kadi.ext.babel import babel
from kadi.ext.celery import celery
from kadi.ext.csrf import csrf
from kadi.ext.db import db
from kadi.ext.elasticsearch import es
from kadi.ext.limiter import limiter
from kadi.ext.login import login
from kadi.ext.migrate import migrate
from kadi.ext.oauth import oauth_registry
from kadi.ext.oauth import oauth_server
from kadi.ext.oauth import oidc_registry
from kadi.ext.talisman import talisman
from kadi.lib.api.core import json_error_response
from kadi.lib.api.utils import is_api_request
from kadi.lib.config.core import get_sys_config
from kadi.lib.conversion import truncate
from kadi.lib.db import SimpleTimestampMixin
from kadi.lib.db import StateTimestampMixin
from kadi.lib.db import has_pending_revisions
from kadi.lib.exceptions import KadiConfigurationError
from kadi.lib.format import duration
from kadi.lib.format import filesize
from kadi.lib.oauth.utils import has_oauth2_providers
from kadi.lib.permissions.core import has_permission
from kadi.lib.permissions.utils import get_object_roles
from kadi.lib.plugins.core import run_hook
from kadi.lib.plugins.core import template_hook
from kadi.lib.plugins.utils import get_plugin_frontend_translations
from kadi.lib.plugins.utils import get_plugin_scripts
from kadi.lib.revisions.core import setup_revisions
from kadi.lib.search.models import SearchableMixin
from kadi.lib.security import hash_value
from kadi.lib.utils import as_list
from kadi.lib.utils import compact_json
from kadi.lib.utils import flatten_list
from kadi.lib.utils import has_capabilities
from kadi.lib.utils import is_http_url
from kadi.lib.web import IdentifierConverter
from kadi.lib.web import flash_danger
from kadi.lib.web import get_locale
from kadi.lib.web import html_error_response
from kadi.lib.web import static_url
from kadi.lib.web import url_for
from kadi.modules.accounts.models import UserState
from kadi.modules.accounts.providers import LocalProvider
from kadi.modules.accounts.providers.core import get_auth_provider
from kadi.modules.accounts.providers.core import init_auth_providers
from kadi.modules.accounts.utils import json_user
from kadi.modules.accounts.utils import logout_user
from kadi.modules.workflows.models import Workflow  # pylint: disable=unused-import
from kadi.plugins import impl
from kadi.plugins import spec

from .config import CONFIG_CLASSES


class KadiRequest(Request):
    """Custom request wrapper class."""

    def _get_file_stream(
        self, total_content_length, content_type, filename=None, content_length=None
    ):
        # Increase the maximum size up to which the temporary file switches from an
        # in-memory buffer to an actual file. Note that this is only relevant for form
        # data.
        return SpooledTemporaryFile(max_size=self.max_content_length, mode="rb+")


class Kadi(Flask):
    """The main application class.

    :param environment: (optional) The environment the application should run in.
        Defaults to the value of the ``KADI_ENV`` environment variable or the production
        environment.
    """

    request_class = KadiRequest

    def __init__(self, import_name, environment=None):
        if environment is None:
            environment = os.environ.get(const.VAR_ENV, const.ENV_PRODUCTION)

        if environment not in {
            const.ENV_PRODUCTION,
            const.ENV_DEVELOPMENT,
            const.ENV_TESTING,
        }:
            raise KadiConfigurationError(
                f"Invalid environment, must be one of '{const.ENV_PRODUCTION}',"
                f" '{const.ENV_DEVELOPMENT}' or '{const.ENV_TESTING}'."
            )

        super().__init__(import_name)

        self.config[const.VAR_ENV] = environment

    @property
    def environment(self):
        """Get the current environment of the application."""
        return self.config[const.VAR_ENV]

    @property
    def base_url(self):
        """Get the static base URL of the application.

        Based on the ``PREFERRED_URL_SCHEME`` and ``SERVER_NAME`` as specified in the
        application's configuration.
        """
        return f"{self.config['PREFERRED_URL_SCHEME']}://{self.config['SERVER_NAME']}"


def create_app(environment=None, config=None):
    """Create a new application object.

    :param environment: (optional) The environment the application should run in. See
        :class:`Kadi`.
    :param config: (optional) Additional configuration dictionary that takes precedence
        over configuration values defined via the configuration file.
    :return: The new application object.
    """
    app = Kadi(__name__, environment=environment)

    _init_config(app, config)
    _init_logging(app)
    _init_plugins(app)
    _init_extensions(app)
    # Initialize Celery for use in both the application and the actual worker processes
    # to start and execute tasks respectively.
    _init_celery(app)
    _init_app(app)
    _init_jinja(app)

    with app.app_context():
        # Close any potential database connections in case the application is forked
        # after initialization, as each process should create its own connection.
        db.engine.dispose()

        # Perform additional plugin initializations.
        run_hook("kadi_post_app_initialization", app=app)

    return app


CONFIG_REQUIRED = [
    "SQLALCHEMY_DATABASE_URI",
    "MISC_UPLOADS_PATH",
    "SERVER_NAME",
    "SECRET_KEY",
]


def _init_config(app, config):
    app.config.from_object(CONFIG_CLASSES[app.environment])

    if os.environ.get(const.VAR_CONFIG):
        app.config.from_envvar(const.VAR_CONFIG)

    if config is not None:
        app.config.update(config)

    # Interpolate all placeholders, and make sure that the paths are always absolute.
    interpolations = {
        "instance_path": os.path.abspath(app.instance_path),
        "root_path": os.path.abspath(app.root_path),
        "static_path": os.path.abspath(app.static_folder),
    }

    for key, value in app.config.items():
        if isinstance(value, str):
            app.config[key] = value.format(**interpolations)

    # If not testing, verify that the most important config values that don't have
    # usable defaults and are not checked elsewhere already have at least been set.
    if not app.testing:
        for key in CONFIG_REQUIRED:
            if not app.config[key]:
                msg = f"The '{key}' configuration value has not been set."

                # Add some additional information if the app was created via the CLI.
                if os.environ.get(const.VAR_CLI) == "1":
                    msg += (
                        " Maybe the Kadi CLI does not have access to the Kadi"
                        " configuration file?"
                    )

                raise KadiConfigurationError(msg)


def _init_logging(app):
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
    log_level = (
        logging.DEBUG if app.environment == const.ENV_DEVELOPMENT else logging.INFO
    )

    # Flasks default handler is a "StreamHandler" writing to the stream specified by the
    # WSGI server or to stderr outside of a request.
    default_handler.setFormatter(formatter)
    app.logger.setLevel(log_level)

    # Setup SMTP logging, if applicable.
    mail_error_logs = app.config["MAIL_ERROR_LOGS"]

    if mail_error_logs:
        auth = None
        secure = None

        if app.config["SMTP_USERNAME"] and app.config["SMTP_PASSWORD"]:
            auth = (app.config["SMTP_USERNAME"], app.config["SMTP_PASSWORD"])

            if app.config["SMTP_USE_TLS"]:
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(app.config["SMTP_HOST"], app.config["SMTP_PORT"]),
            fromaddr=app.config["MAIL_NO_REPLY"],
            toaddrs=mail_error_logs,
            subject=f"[{app.config['MAIL_SUBJECT_HEADER']}] Error log",
            credentials=auth,
            secure=secure,
        )
        mail_handler.setFormatter(formatter)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    # Disable some unwanted non-error logging output.
    logging.getLogger("elastic_transport").setLevel(logging.ERROR)
    logging.getLogger("fpdf.output").setLevel(logging.ERROR)
    logging.getLogger("fontTools.subset").setLevel(logging.ERROR)


def _init_plugins(app):
    plugin_manager = PluginManager("kadi")
    plugin_manager.add_hookspecs(spec)

    # Load all configured plugins that registered themselves via the plugin entry point.
    for plugin in app.config["PLUGINS"]:
        plugin_manager.load_setuptools_entrypoints(const.PLUGIN_ENTRYPOINT, name=plugin)

    # Register all built-in hook implementations.
    plugin_manager.register(impl)

    # Simply store the plugin manager instance on the application instance.
    app.plugin_manager = plugin_manager


def _init_backend_translations(app):
    # See also "kadi.cli.commands.i18n".
    translations_path = app.config["BACKEND_TRANSLATIONS_PATH"]
    plugin_translations_paths = run_hook("kadi_get_translations_paths")

    if plugin_translations_paths:
        # List the main translations path last, so it will take precedence.
        translations_path = f"{';'.join(plugin_translations_paths)};{translations_path}"

    app.config["BABEL_TRANSLATION_DIRECTORIES"] = translations_path


def _get_content_security_policy():
    content_security_policy = {}

    for plugin_csp_config in run_hook("kadi_get_content_security_policies"):
        for key, value in plugin_csp_config.items():
            values = as_list(value)

            if key not in content_security_policy:
                content_security_policy[key] = values
            else:
                for value in values:
                    if value not in content_security_policy[key]:
                        content_security_policy[key].append(value)

    return content_security_policy


def _init_extensions(app):
    # Initialize Flask-Babel.
    with app.app_context():
        _init_backend_translations(app)

    babel.init_app(app, locale_selector=lambda: get_locale().replace("-", "_"))

    # Initialize Flask-Talisman.
    with app.app_context():
        content_security_policy = _get_content_security_policy()

    # HTTPS and the session cookie are handled separately already.
    talisman.init_app(
        app,
        content_security_policy=content_security_policy,
        content_security_policy_nonce_in="script-src",
        force_https=False,
        session_cookie_secure=False,
    )

    # Initialize Sentry.
    sentry_dsn = app.config["SENTRY_DSN"]

    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            release=metadata.version("kadi"),
            environment=app.environment,
        )

    # Initialize all other extensions.
    csrf.init_app(app)
    db.init_app(app)
    es.init_app(app)
    limiter.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db, directory=app.config["MIGRATIONS_PATH"])
    oauth_registry.init_app(app)
    oauth_server.init_app(app)
    oidc_registry.init_app(app)


def _init_celery(app):
    config_prefix = "CELERY_"

    with app.app_context():
        # Retrieve and explicitely register all background tasks.
        tasks = flatten_list(run_hook("kadi_get_background_tasks"))

        for task in tasks:
            celery.tasks.register(task)

        # Retrieve and merge all background task schedules.
        schedules = run_hook("kadi_get_background_task_schedules")
        beat_schedule = {}

        for schedule in schedules:
            beat_schedule.update(**schedule)

        app.config["CELERY_BEAT_SCHEDULE"] = beat_schedule

    for key, value in app.config.items():
        if key.startswith(config_prefix):
            setattr(celery.conf, key[len(config_prefix) :].lower(), value)

    class ContextTask(celery.Task):
        """Wrapper for tasks to run inside their own application context."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


def _error_handler(e):
    # Do not show error information to unauthenticated users, except for errors related
    # to CSRF, rate limits and server errors.
    if (
        not isinstance(e, (CSRFError, RateLimitExceeded))
        and not e.code >= 500
        and not current_user.is_authenticated
    ):
        return current_app.login_manager.unauthorized()

    # Ensure that all relevant Flask-Talisman request handlers are always called, even
    # if another pre-request handler raises an exception.
    talisman._make_nonce()

    description = e.description if isinstance(e, CSRFError) else None

    if is_api_request():
        response = json_error_response(e.code, description=description)
    else:
        response = html_error_response(e.code, description=description)

    talisman._set_response_headers(response)
    return response


def _before_request_handler():
    if not current_user.is_authenticated:
        session.pop(const.SESSION_KEY_COLLECTION_CONTEXT, None)
        return None

    session.pop(const.SESSION_KEY_NEXT_URL, None)
    session.pop(const.SESSION_KEY_OIDC_DATA, None)

    inactive_error_msg = _("This account is currently inactive.")

    # If the current user was merged or does not have a valid (current) identity, they
    # are logged out completely.
    if (
        current_user.is_merged
        or current_user.identity is None
        or current_user.identity.type not in current_app.config["AUTH_PROVIDERS"]
    ):
        redirect_url = logout_user()

        if is_api_request():
            return json_error_response(401, description=inactive_error_msg)

        flash_danger(inactive_error_msg)
        return redirect(redirect_url)

    # These endpoints should still work even if the current user needs email
    # confirmation, is inactive or needs to accept the legal notices before proceeding.
    if request.endpoint in {
        "accounts.logout",
        "main.about",
        "main.help",
        "main.terms_of_use",
        "main.privacy_policy",
        "main.legal_notice",
        "static",
    }:
        return None

    # Check if the current user's latest identity needs email confirmation. We check
    # this before the user state, so inactive users can still confirm their email
    # address.
    if current_user.identity.needs_email_confirmation:
        endpoint = "accounts.request_email_confirmation"

        if request.endpoint in {endpoint, "accounts.confirm_email"}:
            return None

        if is_api_request():
            return json_error_response(
                401, description="Please confirm your email address."
            )

        return redirect(url_for(endpoint))

    # Check if the state of the current user is active.
    if current_user.state != UserState.ACTIVE:
        endpoint = "accounts.inactive_user"

        if request.endpoint == endpoint:
            return None

        if is_api_request():
            return json_error_response(401, description=inactive_error_msg)

        return redirect(url_for(endpoint))

    # Check if the current user needs to accept the legal notices.
    if current_user.needs_legals_acceptance:
        endpoint = "accounts.request_legals_acceptance"

        if request.endpoint == endpoint:
            return None

        if is_api_request():
            return json_error_response(
                401, description="Please accept all legal notices."
            )

        return redirect(url_for(endpoint))

    return None


def _after_request_handler(response):
    # Customize the returned headers when a rate limit has been reached.
    current_limit = limiter.current_limit

    if current_limit is not None and current_limit.breached:
        response.headers["Retry-After"] = math.ceil(
            current_limit.reset_at - time.time()
        )

    return response


def _init_storage_providers(app):
    storage_providers = {}

    for storage_provider in flatten_list(run_hook("kadi_get_storage_providers")):
        storage_type = storage_provider.storage_type

        if storage_type not in storage_providers:
            storage_providers[storage_type] = storage_provider
        else:
            app.logger.warn(
                f"A storage provider of type '{storage_type}' is already registered."
            )

    app.config["STORAGE_PROVIDERS"] = storage_providers

    # Check if the configured storage provider type is valid.
    configured_provider = app.config["STORAGE_PROVIDER"]

    if configured_provider not in storage_providers:
        raise KadiConfigurationError(
            f"No storage provider found for storage type '{configured_provider}'."
        )


def _check_database(app):
    # If in a production environment and the app was not created via the CLI, check for
    # pending database revisions. Certain CLI commands may still perform this check
    # separately, regardless of environment, if required.
    if app.environment == const.ENV_PRODUCTION and os.environ.get(const.VAR_CLI) != "1":
        if has_pending_revisions():
            raise KadiConfigurationError(
                "The database schema is not up to date. Maybe you forgot to run 'kadi"
                " db upgrade'?"
            )


def _init_app(app):
    # Define a maximum content length based on various maximum sizes as well as some
    # additional padding.
    max_content_length = max(
        const.UPLOAD_CHUNK_SIZE,
        const.UPLOAD_CHUNKED_BOUNDARY,
        const.IMAGE_MAX_SIZE,
        const.IMPORT_MAX_SIZE,
    )
    app.config["MAX_CONTENT_LENGTH"] = max_content_length + const.ONE_MB

    # Set up the manifest mapping, see also "kadi.cli.commands.assets".
    manifest_path = app.config["MANIFEST_PATH"]

    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            app.config["MANIFEST_MAPPING"] = json.load(f)

    # Automatically enable all workflow features when experimental features are enabled.
    if app.config["EXPERIMENTAL_FEATURES"]:
        app.config["WORKFLOW_FEATURES"] = True

    # Set up a middleware to handle the amount of trusted "X-Forwarded-*" header values,
    # if applicable.
    if app.config["PROXY_FIX_HEADERS"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, **app.config["PROXY_FIX_HEADERS"])

    # Register a global error handler for all exceptions.
    app.register_error_handler(HTTPException, _error_handler)

    # Register global before and after request handlers.
    app.before_request(_before_request_handler)
    app.after_request(_after_request_handler)

    # Register custom URL converters.
    app.url_map.converters["identifier"] = IdentifierConverter

    # Perform various initializations based on returned plugin results.
    with app.app_context():
        capabilities = flatten_list(run_hook("kadi_get_capabilities"))
        app.config["CAPABILITIES"] = set(capabilities)

        run_hook("kadi_register_oauth2_providers", registry=oauth_registry)

        _init_storage_providers(app)

        for bp in flatten_list(run_hook("kadi_get_blueprints")):
            app.register_blueprint(bp)

    # Perform all remaining initializations.
    setup_revisions()
    init_auth_providers(app)

    if app.config["ELASTICSEARCH_HOSTS"]:
        SearchableMixin.register_search_listeners()

    SimpleTimestampMixin.register_timestamp_listener()
    StateTimestampMixin.register_timestamp_listener()

    # Check if the database is up to date, if applicable.
    with app.app_context():
        _check_database(app)

    # Setup some values that will be imported automatically when running "kadi shell".
    @app.shell_context_processor
    def _shell_context():
        return {"const": const}


def _init_jinja(app):
    # Register all custom extensions.
    app.jinja_env.add_extension("kadi.lib.jinja.SnippetExtension")

    # Provide global access to various functions and modules.
    app.jinja_env.globals.update(
        {
            "allow_registration": LocalProvider.allow_registration,
            "any": any,
            "bool": bool,
            "const": const,
            "environment": app.environment,
            "get_auth_provider": get_auth_provider,
            "get_locale": get_locale,
            "get_object_roles": get_object_roles,
            "get_plugin_frontend_translations": get_plugin_frontend_translations,
            "get_plugin_scripts": get_plugin_scripts,
            "get_sys_config": get_sys_config,
            "has_capabilities": has_capabilities,
            "has_oauth2_providers": has_oauth2_providers,
            "has_permission": has_permission,
            "hash_value": hash_value,
            "is_http_url": is_http_url,
            "json_user": json_user,
            "partial": partial,
            "len": len,
            "list": list,
            "reversed": reversed,
            "sorted": sorted,
            "static_url": static_url,
            "template_hook": template_hook,
            "url_for": url_for,
            "version": metadata.version("kadi"),
            "UserState": UserState,
        }
    )

    json_dumps_func = partial(compact_json, ensure_ascii=True, sort_keys=False)

    # Register all globally used custom filters.
    app.jinja_env.filters.update(
        {
            "duration": duration,
            "filesize": filesize,
            "number": format_number,
            "tojson_escaped": json_dumps_func,
            "truncate": truncate,
        }
    )

    # Configure some custom policies.
    app.jinja_env.policies["json.dumps_function"] = json_dumps_func
    app.jinja_env.policies["json.dumps_kwargs"] = {}
    # Needs to be specified in addition to the Babel configuration.
    app.jinja_env.policies["ext.i18n.trimmed"] = True
