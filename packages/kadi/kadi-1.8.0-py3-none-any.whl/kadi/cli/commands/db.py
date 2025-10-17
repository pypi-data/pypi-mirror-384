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
import sys
from functools import wraps

import click
from flask import current_app
from flask_migrate import downgrade as downgrade_db
from flask_migrate import upgrade as upgrade_db

from kadi.cli.main import kadi
from kadi.cli.utils import check_env
from kadi.cli.utils import echo
from kadi.cli.utils import echo_danger
from kadi.cli.utils import echo_success
from kadi.cli.utils import echo_warning
from kadi.ext.db import db as database
from kadi.lib.db import update_object
from kadi.lib.licenses.core import get_builtin_licenses
from kadi.lib.licenses.core import get_plugin_licenses
from kadi.lib.licenses.models import License
from kadi.lib.licenses.utils import initialize_builtin_licenses
from kadi.lib.permissions.utils import initialize_system_roles
from kadi.modules.accounts.providers import LocalProvider
from kadi.modules.collections.core import create_collection
from kadi.modules.collections.models import CollectionVisibility
from kadi.modules.groups.core import create_group
from kadi.modules.groups.models import GroupVisibility
from kadi.modules.records.core import create_record
from kadi.modules.records.models import RecordVisibility
from kadi.modules.templates.core import create_template
from kadi.modules.templates.models import TemplateType
from kadi.modules.templates.models import TemplateVisibility


@kadi.group()
def db():
    """Utility commands for database management."""


def _initialize_db():
    if initialize_system_roles():
        echo("Initialized system roles.")

    if initialize_builtin_licenses():
        echo("Initialized built-in licenses.")


@db.command()
@click.argument("revision", default="head")
def upgrade(revision):
    """Upgrade the database schema to a specified revision.

    The default behavior is to upgrade to the latest revision.
    """
    upgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision=revision)

    database.session.commit()
    echo_success("Upgrade completed successfully.")


@db.command()
@click.argument("revision", default="-1")
@click.option("--i-am-sure", is_flag=True)
@check_env
def downgrade(revision, i_am_sure):
    """Downgrade the database schema to a specified revision.

    The default behavior is to downgrade a single revision.
    """
    if not i_am_sure:
        echo_warning(
            "This can potentially erase some data of database"
            f" '{current_app.config['SQLALCHEMY_DATABASE_URI']}'. If you are sure you"
            " want to do this, use the flag --i-am-sure."
        )
        sys.exit(1)

    downgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision=revision)

    database.session.commit()
    echo_success("Downgrade completed successfully.")


@db.command()
def init():
    """Initialize the database."""
    upgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision="head")
    _initialize_db()

    database.session.commit()
    echo_success("Initialization completed successfully.")


@db.command()
@click.option("--i-am-sure", is_flag=True)
@check_env
def reset(i_am_sure):
    """Reset and reinitialize the database."""
    if not i_am_sure:
        echo_warning(
            "This will erase all data of database"
            f" '{current_app.config['SQLALCHEMY_DATABASE_URI']}'. If you are sure you"
            " want to do this, use the flag --i-am-sure."
        )
        sys.exit(1)

    downgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision="base")
    upgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision="head")
    _initialize_db()

    database.session.commit()
    echo_success("Reset completed successfully.")


@db.command()
def licenses():
    """Update the plugin licenses stored in the database.

    Note that plugin licenses that have previously been added to the database, but are
    not included in the current plugin licenses anymore, will only be deleted if they
    are not in use by any record.
    """
    builtin_licenses = get_builtin_licenses()
    plugin_licenses = get_plugin_licenses()

    for license in License.query.order_by(License.name):
        # Check if the current license is a deprecated plugin license.
        if license.name not in builtin_licenses and license.name not in plugin_licenses:
            current_records = license.records.count()

            echo_warning(
                f"Found deprecated license '{license.name}' in database, which is"
                f" currently used by {current_records} record(s)."
            )

            # Keep licenses that are still in use.
            if current_records == 0:
                database.session.delete(license)
                echo(f"Deleted license '{license.name}'.")

    # Update the current plugin licenses.
    for name, license_meta in plugin_licenses.items():
        license = License.query.filter_by(name=name).first()

        title = license_meta["title"]
        url = license_meta["url"]

        if license is None:
            License.create(name=name, title=title, url=url)
            echo(f"Added new license '{name}'.")
        else:
            if name in builtin_licenses:
                echo_warning(f"License '{name}' is built-in and cannot be changed.")
            else:
                update_object(license, title=title, url=url)
                echo(f"Updated license '{name}'.")

    database.session.commit()
    echo_success("Licenses updated successfully.")


SAMPLE_EXTRAS = [
    {"type": "str", "key": "Sample str", "value": "sample"},
    {"type": "int", "key": "Sample integer", "value": 9, "unit": "h"},
    {"type": "float", "key": "Sample float", "value": 3.141, "unit": "cm"},
    {"type": "bool", "key": "Sample boolean", "value": True},
    {
        "type": "date",
        "key": "Sample date",
        "value": "2020-01-01T12:34:56.789000+00:00",
    },
    {
        "type": "dict",
        "key": "Sample dict",
        "value": [{"type": "str", "key": "Nested value", "value": None}],
    },
    {
        "type": "list",
        "key": "Sample list",
        "value": [{"type": "float", "value": 1e123, "unit": None}],
    },
    {
        "type": "str",
        "key": "Sample validation",
        "value": "sample 1",
        "validation": {"required": True, "options": ["sample 1", "sample 2"]},
    },
]


SAMPLE_TEMPLATE_DATA = {
    TemplateType.RECORD: {
        "title": "Sample title",
        "identifier": "sample-identifier",
        "description": "This is a *sample* description.",
        "license": "CC-BY-4.0",
        "extras": SAMPLE_EXTRAS,
        "tags": ["sample", "sample record"],
        "type": "sample",
    },
    TemplateType.EXTRAS: SAMPLE_EXTRAS,
}


def _counting(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(wrapper, "count"):
            wrapper.count = 0

        wrapper.count += 1

        return func(*args, **kwargs, count=wrapper.count)

    return wrapper


def _create_user(username, system_role, is_sysadmin=False):
    user = LocalProvider.register(
        displayname=username.capitalize(),
        username=username,
        email=f"{username}@example.com",
        password=username,
        system_role=system_role,
        apply_role_rules=False,
    ).user

    if is_sysadmin:
        user.is_sysadmin = True

    return user


# pylint: disable=dangerous-default-value
@_counting
def _create_record(
    creator,
    type="sample",
    description="This is a *sample* record.",
    license="CC-BY-4.0",
    extras=SAMPLE_EXTRAS,
    tags=["sample", "sample record"],
    visibility=RecordVisibility.PRIVATE,
    **kwargs,
):
    create_record(
        creator=creator,
        identifier=f"sample-record-{kwargs['count']}",
        title=f"Sample record {kwargs['count']}",
        type=type,
        description=description,
        license=license,
        extras=extras,
        tags=tags,
        visibility=visibility,
    )


# pylint: disable=dangerous-default-value
@_counting
def _create_collection(
    creator,
    description="This is a *sample* collection.",
    tags=["sample", "sample collection"],
    visibility=CollectionVisibility.PRIVATE,
    **kwargs,
):
    create_collection(
        creator=creator,
        identifier=f"sample-collection-{kwargs['count']}",
        title=f"Sample collection {kwargs['count']}",
        description=description,
        tags=tags,
        visibility=visibility,
    )


@_counting
def _create_template(
    creator,
    type,
    data=None,
    description="This is a *sample* template.",
    visibility=TemplateVisibility.PRIVATE,
    **kwargs,
):
    data = data if data is not None else SAMPLE_TEMPLATE_DATA[type]

    create_template(
        creator=creator,
        type=type,
        data=data,
        identifier=f"sample-template-{kwargs['count']}",
        title=f"Sample template {kwargs['count']}",
        description=description,
        visibility=visibility,
    )


@_counting
def _create_group(
    creator,
    description="This is a *sample* group.",
    visibility=GroupVisibility.PRIVATE,
    **kwargs,
):
    create_group(
        creator=creator,
        identifier=f"sample-group-{kwargs['count']}",
        title=f"Sample group {kwargs['count']}",
        description=description,
        visibility=visibility,
    )


@db.command()
@click.option("--i-am-sure", is_flag=True)
@check_env
def sample_data(i_am_sure):
    """Reset the database and setup some sample users and resources."""
    if not i_am_sure:
        echo_warning(
            "This will erase all data of database"
            f" '{current_app.config['SQLALCHEMY_DATABASE_URI']}' and replace it with"
            " sample data. If you are sure you want to do this, use the flag"
            " --i-am-sure."
        )
        sys.exit(1)

    downgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision="base")
    upgrade_db(directory=current_app.config["MIGRATIONS_PATH"], revision="head")
    _initialize_db()

    if not LocalProvider.is_registered():
        echo_danger("The local provider is not registered in the application.")
        sys.exit(1)

    echo("Setting up sample users...")

    user = _create_user("user", system_role="member", is_sysadmin=True)
    admin = _create_user("admin", system_role="admin")
    member = _create_user("member", system_role="member")
    _create_user("guest", system_role="guest")

    echo("Setting up sample records...")

    for _user in [admin, member]:
        _create_record(_user)
        _create_record(_user, visibility=RecordVisibility.PUBLIC)

    _create_record(user, type=None)
    _create_record(user, description="")
    _create_record(user, license=None)
    _create_record(user, extras=[])
    _create_record(user, tags=None)
    _create_record(user, tags=["sample"])
    _create_record(user, visibility=RecordVisibility.PUBLIC)
    _create_record(user)

    echo("Setting up sample collections...")

    for _user in [admin, member]:
        _create_collection(_user)
        _create_collection(_user, visibility=CollectionVisibility.PUBLIC)

    _create_collection(user, description="")
    _create_collection(user, tags=None)
    _create_collection(user, tags=["sample"])
    _create_collection(user, visibility=CollectionVisibility.PUBLIC)
    _create_collection(user)

    echo("Setting up sample templates...")

    for _user in [admin, member]:
        for template_type in [TemplateType.RECORD, TemplateType.EXTRAS]:
            _create_template(_user, type=template_type)
            _create_template(
                _user, type=template_type, visibility=TemplateVisibility.PUBLIC
            )

    for template_type in [TemplateType.RECORD, TemplateType.EXTRAS]:
        _create_template(user, type=template_type, description="")
        _create_template(user, type=template_type, visibility=TemplateVisibility.PUBLIC)
        _create_template(user, type=template_type)

    echo("Setting up sample groups...")

    for _user in [admin, member]:
        _create_group(_user)
        _create_group(_user, visibility=GroupVisibility.PUBLIC)

    _create_group(user, description="")
    _create_group(user, visibility=GroupVisibility.PUBLIC)
    _create_group(user)

    database.session.commit()
    echo_success("Setup completed successfully.")
