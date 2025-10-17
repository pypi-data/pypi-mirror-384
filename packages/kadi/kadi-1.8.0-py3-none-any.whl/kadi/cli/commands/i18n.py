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
import sys

import click
from flask import current_app

import kadi.lib.constants as const
from kadi.cli.main import kadi
from kadi.cli.utils import echo_danger
from kadi.cli.utils import echo_success
from kadi.cli.utils import echo_warning
from kadi.cli.utils import run_command
from kadi.lib.plugins.core import run_hook


@kadi.group()
def i18n():
    """Utility commands for managing translations."""


def _pybabel_extract(translations_path, workdir):
    cwd = os.getcwd()

    if workdir is None:
        workdir = os.path.dirname(translations_path)

    os.chdir(workdir)

    babel_cfg = os.path.join(translations_path, "babel.cfg")
    pot_path = os.path.join(translations_path, "messages.pot")
    extract_cmd = [
        "pybabel",
        "extract",
        "-F",
        babel_cfg,
        "-o",
        pot_path,
        "-k",
        "lazy_gettext",
        "-k",
        "_l",
        "--no-wrap",
        "--no-location",
        "--sort-output",
        ".",
    ]
    run_command(extract_cmd)

    os.chdir(cwd)


def _load_plugins():
    os.environ[const.VAR_API_BP] = "1"

    # Always load all plugins, even if not configured, since they might specify a custom
    # translations path.
    current_app.plugin_manager.load_setuptools_entrypoints(const.PLUGIN_ENTRYPOINT)


def _get_translations_path(plugin_name):
    if plugin_name is not None:
        plugin = current_app.plugin_manager.get_plugin(plugin_name)

        if plugin is not None:
            if hasattr(plugin, "kadi_get_translations_paths"):
                return plugin.kadi_get_translations_paths()

            echo_danger("The given plugin does not specify a translations path.")
        else:
            echo_danger("No plugin with that name could be found.")

        sys.exit(1)

    return current_app.config["BACKEND_TRANSLATIONS_PATH"]


plugin_option = click.option(
    "-p", "--plugin", help="The name of a plugin to use instead."
)

workdir_option = click.option(
    "-w",
    "--workdir",
    help="The working directory to run the message extraction process in, which is"
    ' relevant for the extraction patterns and paths defined in "babel.cfg". Defaults'
    " to the parent directory of the translations path.",
)


@i18n.command()
@click.argument("lang")
@plugin_option
@workdir_option
@click.option("--i-am-sure", is_flag=True)
def init(lang, plugin, workdir, i_am_sure):
    """Add the given language to the backend translations."""
    if not i_am_sure:
        echo_warning(
            f"This might replace existing translations for language '{lang}'. If you"
            " are sure you want to do this, use the flag --i-am-sure."
        )
        sys.exit(1)

    _load_plugins()

    translations_path = _get_translations_path(plugin)
    _pybabel_extract(translations_path, workdir)

    pot_path = os.path.join(translations_path, "messages.pot")
    init_cmd = ["pybabel", "init", "-i", pot_path, "-d", translations_path, "-l", lang]
    run_command(init_cmd)

    echo_success("Initialization completed successfully.")


@i18n.command()
@plugin_option
@workdir_option
def update(plugin, workdir):
    """Update the existing backend translations."""
    _load_plugins()

    translations_path = _get_translations_path(plugin)
    _pybabel_extract(translations_path, workdir)

    pot_path = os.path.join(translations_path, "messages.pot")
    update_cmd = [
        "pybabel",
        "update",
        "-i",
        pot_path,
        "-d",
        translations_path,
        "-N",
        "--no-wrap",
    ]
    run_command(update_cmd)

    echo_success("Update completed successfully.")


@i18n.command()
def compile():
    """Compile all existing backend translations, including plugins."""
    _load_plugins()

    translations_paths = [current_app.config["BACKEND_TRANSLATIONS_PATH"]] + run_hook(
        "kadi_get_translations_paths"
    )

    for path in translations_paths:
        compile_cmd = ["pybabel", "compile", "-d", path]
        run_command(compile_cmd)

    echo_success("Compilation completed successfully.")
