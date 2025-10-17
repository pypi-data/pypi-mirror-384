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
import os
import subprocess

import click
from flask import current_app

from kadi.cli.main import kadi
from kadi.cli.utils import check_database


# This wrapper command ensures that the correct Flask application and debug mode are
# always being used.
@kadi.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
@click.pass_context
def run(ctx):
    """Wrapper command for the Flask development server.

    For a list of additional parameters that can be passed to the development server,
    please run "flask run --help".
    """
    check_database()

    app_path = os.path.join(current_app.root_path, "wsgi.py")
    excluded_dirs = ["build", "dist", "docs", "node_modules", "tests"]

    try:
        # Running the dev server in a subprocess allows it to function the same as when
        # running it via the Flask CLI, i.e. the dev server will not crash on syntax
        # errors or invalid imports.
        subprocess.run(
            [
                "flask",
                "--app",
                app_path,
                "--debug",
                "run",
                "--exclude-patterns",
                os.path.pathsep.join(f"*/{d}/*" for d in excluded_dirs),
                *ctx.args,
            ]
        )
    except KeyboardInterrupt:
        pass
