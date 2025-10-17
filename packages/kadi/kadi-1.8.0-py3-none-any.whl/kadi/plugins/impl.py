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


# pylint: disable=missing-function-docstring


from celery.schedules import crontab
from flask import current_app
from flask import render_template
from flask_babel import gettext as _

import kadi.lib.constants as const
from kadi.lib.api.blueprint import bp as api_bp
from kadi.lib.federation import get_federated_instances
from kadi.lib.mails.tasks import _send_mail_task
from kadi.lib.oauth.utils import get_refresh_token_handler
from kadi.lib.permissions.tasks import _apply_role_rules_task
from kadi.lib.resources.tasks import _publish_resource_task
from kadi.lib.resources.tasks import _purge_resources_task
from kadi.lib.storage.local import LocalStorage
from kadi.lib.tasks.models import TaskState
from kadi.modules.accounts.blueprint import bp as accounts_bp
from kadi.modules.accounts.tasks import _merge_users_task
from kadi.modules.collections.blueprint import bp as collections_bp
from kadi.modules.groups.blueprint import bp as groups_bp
from kadi.modules.main.blueprint import bp as main_bp
from kadi.modules.main.tasks import _periodic_cleanup_task
from kadi.modules.records.blueprint import bp as records_bp
from kadi.modules.records.dashboards import (
    get_custom_mimetype as get_dashboard_mimetype,
)
from kadi.modules.records.previews import get_builtin_preview_data
from kadi.modules.records.tasks import _merge_chunks_task
from kadi.modules.records.tasks import _purge_record_task
from kadi.modules.settings.blueprint import bp as settings_bp
from kadi.modules.sysadmin.blueprint import bp as sysadmin_bp
from kadi.modules.templates.blueprint import bp as templates_bp
from kadi.modules.workflows.blueprint import bp as workflows_bp
from kadi.modules.workflows.core import get_custom_mimetype as get_workflow_mimetype

from . import hookimpl


@hookimpl(tryfirst=True)
def kadi_get_blueprints():
    blueprints = [
        api_bp,
        accounts_bp,
        collections_bp,
        groups_bp,
        main_bp,
        records_bp,
        settings_bp,
        sysadmin_bp,
        templates_bp,
    ]

    if current_app.config["WORKFLOW_FEATURES"]:
        import kadi.modules.workflows.api  # pylint: disable=unused-import

        blueprints.append(workflows_bp)

    return blueprints


@hookimpl(tryfirst=True)
def kadi_get_content_security_policies():
    return {
        "default-src": "'self'",
        "base-uri": "'none'",
        "frame-ancestors": "'self'",
        "frame-src": "'self'",
        "img-src": ["'self'", "blob:", "data:"],
        "object-src": "'none'",
        "script-src": ["'self'", "'unsafe-eval'"],
        "style-src": ["'self'", "'unsafe-inline'", "data:"],
    }


@hookimpl(tryfirst=True)
def kadi_get_custom_mimetype(file, base_mimetype):
    for get_custom_mimetype in [get_workflow_mimetype, get_dashboard_mimetype]:
        custom_mimetype = get_custom_mimetype(file, base_mimetype)

        if custom_mimetype:
            return custom_mimetype

    return None


@hookimpl
def kadi_get_oauth2_providers():
    description = _(
        "Connecting your account to this external Kadi4Mat instance makes it possible"
        " to use it in federated search of different resources."
    )
    providers = []

    for instance in get_federated_instances():
        providers.append(
            {"description": description, "website": instance["url"], **instance}
        )

    return providers


@hookimpl(tryfirst=True)
def kadi_get_preview_data(file):
    return get_builtin_preview_data(file)


@hookimpl(tryfirst=True)
def kadi_get_preview_templates(file):
    return render_template("records/snippets/preview_file.html", file=file)


@hookimpl(tryfirst=True)
def kadi_get_storage_providers():
    storage_path = current_app.config["STORAGE_PATH"]

    if storage_path is None:
        return None

    return LocalStorage(storage_path)


@hookimpl
def kadi_get_background_tasks():
    return [
        _apply_role_rules_task,
        _merge_chunks_task,
        _merge_users_task,
        _periodic_cleanup_task,
        _publish_resource_task,
        _purge_record_task,
        _purge_resources_task,
        _send_mail_task,
    ]


@hookimpl(tryfirst=True)
def kadi_get_background_task_notification(task):
    if task.name != const.TASK_PUBLISH_RESOURCE:
        return None

    body = None

    if task.state == TaskState.RUNNING:
        body = render_template(
            "notifications/publish_resource.html", progress=task.progress
        )
    elif task.state in {TaskState.SUCCESS, TaskState.FAILURE}:
        template = task.result.get("template") if task.result is not None else None
        body = template if template is not None else _("Unexpected error.")

    return _("Publish resource"), body


@hookimpl
def kadi_get_background_task_schedules():
    return {
        "periodic-cleanup": {
            "task": const.TASK_PERIODIC_CLEANUP,
            "schedule": crontab(minute="*/60"),
        },
    }


@hookimpl
def kadi_register_oauth2_providers(registry):
    for instance in get_federated_instances(include_credentials=True):
        client_id = instance["client_id"]
        client_secret = instance["client_secret"]
        base_url = instance["url"]

        registry.register(
            name=instance["name"],
            client_id=client_id,
            client_secret=client_secret,
            access_token_url=f"{base_url}/oauth/token",
            access_token_params={
                "client_id": client_id,
                "client_secret": client_secret,
            },
            authorize_url=f"{base_url}/oauth/authorize",
            api_base_url=f"{base_url}/api/v1/",
            compliance_fix=get_refresh_token_handler(client_id, client_secret),
        )
