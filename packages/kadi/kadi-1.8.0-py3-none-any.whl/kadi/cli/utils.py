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
import subprocess
import sys
from functools import wraps

import click
from flask import current_app

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import has_pending_revisions


def check_env(func):
    """Decorator to check if a command is run inside a production environment.

    This can prevent potentially unsafe commands to be accidentally run when working
    inside a production environment. The environment that is checked is the one the
    current app is configured with. A command may still be run by using the --force
    flag.
    """
    click.option(
        "--force",
        is_flag=True,
        help="Force this command to run even if inside a production environment.",
    )(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        force = kwargs.pop("force", False)

        if current_app.environment == const.ENV_PRODUCTION:
            if force:
                func(*args, **kwargs)
            else:
                echo_warning(
                    "This command should normally not be run in a production"
                    " environment. If you want to run it regardless, use the flag"
                    " --force."
                )
        else:
            func(*args, **kwargs)

    return wrapper


def check_database():
    """Check if the database is reachable and has no pending revisions."""
    if has_pending_revisions():
        echo_danger(
            "The database schema is not up to date. Maybe you forgot to run 'kadi db"
            " upgrade'?"
        )
        sys.exit(1)

    # See the main application factory function on why this call is necessary.
    db.engine.dispose()


def run_command(cmd):
    """Run an external command and exit if it returns a non-zero status code.

    :param cmd: The command to run as a list of arguments.
    """
    result = subprocess.run(cmd)

    if result.returncode != 0:
        sys.exit(result.returncode)


def echo(msg="", **kwargs):
    r"""Print a styled message to a file or stdout.

    Wraps Click's ``secho`` function.

    :param msg: (optional) The message to print.
    :param \**kwargs: Additional keyword arguments to pass to ``secho``.
    """
    click.secho(msg, **kwargs)


def echo_danger(msg="", **kwargs):
    r"""Print an error message to a file or stdout.

    Uses :func:`echo` with a fixed red foreground color.

    :param msg: (optional) See :func:`echo`.
    :param \**kwargs: See :func:`echo`.
    """
    echo(msg, fg="red", **kwargs)


def echo_success(msg="", **kwargs):
    r"""Print a success message to a file or stdout.

    Uses :func:`echo` with a fixed green foreground color.

    :param msg: (optional) See :func:`echo`.
    :param \**kwargs: See :func:`echo`.
    """
    echo(msg, fg="green", **kwargs)


def echo_warning(msg="", **kwargs):
    r"""Print a warning message to a file or stdout.

    Uses :func:`echo` with a fixed yellow foreground color.

    :param msg: (optional) See :func:`echo`.
    :param \**kwargs: See :func:`echo`.
    """
    echo(msg, fg="yellow", **kwargs)
