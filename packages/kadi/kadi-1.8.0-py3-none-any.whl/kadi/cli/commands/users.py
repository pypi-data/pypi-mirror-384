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

import click

from kadi.cli.main import kadi
from kadi.cli.utils import echo
from kadi.cli.utils import echo_danger
from kadi.cli.utils import echo_success
from kadi.ext.db import db
from kadi.lib.security import random_alnum
from kadi.modules.accounts.forms import CreateLocalUserForm
from kadi.modules.accounts.models import User
from kadi.modules.accounts.models import UserState
from kadi.modules.accounts.providers import LocalProvider


@kadi.group()
def users():
    """Utility commands for managing users."""


@users.command()
@click.option("-d", "--displayname", help="The display name of the user.")
@click.option("-u", "--username", help="The unique username of the user.")
@click.option("-e", "--email", help="The email address of the user.")
@click.option(
    "-y",
    "--yes",
    "force",
    is_flag=True,
    help="Automatically accept the confirmation prompt to create the user.",
)
def create(displayname, username, email, force):
    """Create a new local user."""
    if not LocalProvider.is_registered():
        echo_danger("The local provider is not registered in the application.")
        sys.exit(1)

    is_interactive = displayname is None or username is None or email is None

    displayname_field = "displayname"
    username_field = "username"
    email_field = "email"

    if username is None:
        username = click.prompt(username_field.capitalize())

    if displayname is None:
        displayname = click.prompt(displayname_field.capitalize(), default=username)

    if email is None:
        email = click.prompt(email_field.capitalize())

    form = CreateLocalUserForm(
        meta={"csrf": False},
        data={
            displayname_field: displayname,
            username_field: username,
            email_field: email,
        },
    )

    if not form.validate():
        for field in [username_field, displayname_field, email_field]:
            for error in form.errors.get(field, []):
                echo_danger(f"[{field.capitalize()}] {error}")

        sys.exit(1)

    if not force:
        if is_interactive:
            echo()

        echo(f"{displayname_field.capitalize():12s}{form.displayname.data}")
        echo(f"{username_field.capitalize():12s}{form.username.data}")
        echo(f"{email_field.capitalize():12s}{form.email.data}")

    if force or click.confirm("Do you want to create this user?"):
        password = random_alnum()
        identity = LocalProvider.register(
            displayname=form.displayname.data,
            username=form.username.data,
            email=form.email.data,
            password=password,
        )

        if not force or is_interactive:
            echo()

        if identity is not None:
            echo_success(f"User with ID {identity.user.id} created successfully.")
            echo(f"Initial user password: {password}")
        else:
            echo_danger("Error creating user.")
            sys.exit(1)


def _get_user_by_id(user_id):
    user = User.query.get(user_id)

    if user is None:
        echo_danger(f"No valid user found with ID {user_id}.")
        sys.exit(1)

    echo(f"Found user with ID {user_id} with the following identities:")

    for identity in user.identities.order_by("created_at"):
        echo(f"  * {identity!r}")

    return user


@users.command()
@click.argument("user_id", type=int)
def state(user_id):
    """Toggle the state of a user."""
    user = _get_user_by_id(user_id)

    if user.state == UserState.ACTIVE:
        prompt = "\nDo you want to to deactivate this user?"
        new_user_state = UserState.INACTIVE
    else:
        prompt = "\nDo you want to to activate this user?"
        new_user_state = UserState.ACTIVE

    if click.confirm(prompt):
        user.state = new_user_state
        db.session.commit()

        echo_success("User updated successfully.")


@users.command()
@click.argument("user_id", type=int)
def sysadmin(user_id):
    """Toggle the sysadmin status of a user."""
    user = _get_user_by_id(user_id)

    if user.is_sysadmin:
        prompt = "\nDo you want to remove the sysadmin status of this user?"
    else:
        prompt = "\nDo you want to set this user as a sysadmin?"

    if click.confirm(prompt):
        user.is_sysadmin = not user.is_sysadmin
        db.session.commit()

        echo_success("User updated successfully.")
