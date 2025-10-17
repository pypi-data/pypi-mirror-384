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
from flask import Blueprint
from flask import current_app
from flask import request
from flask_login import current_user
from markupsafe import Markup
from werkzeug.utils import send_from_directory

from kadi.lib.forms import BaseConfigForm


class PluginBlueprint(Blueprint):
    """Custom Flask blueprint for use in plugins.

    Ensures that static files are handled correctly by always disabling "X-Sendfile", as
    using it would require further configuration outside of the scope of the plugin.
    """

    def send_static_file(self, filename):
        if not self.has_static_folder:
            raise RuntimeError("'static_folder' must be set to serve static_files.")

        max_age = self.get_send_file_max_age(filename)

        if max_age is None:
            max_age = current_app.get_send_file_max_age

        # Use Werkzeug's "send_from_directory" function directly so we can disable
        # "X-Sendfile" for this response.
        return send_from_directory(
            self.static_folder,
            filename,
            max_age=max_age,
            environ=request.environ,
            use_x_sendfile=False,
            response_class=current_app.response_class,
            _root_path=current_app.root_path,
        )


class PluginConfigForm(BaseConfigForm):
    """Form class for use in setting plugin preferences as config items.

    :param plugin_name: The unique name of the plugin, which is also passed to
        :class:`.BaseConfigForm` as ``key_prefix`` and ``suffix``.
    :param user: (optional) The user to pass to :class:`.BaseConfigForm`. Defaults to
        the current user.
    """

    def __init__(self, plugin_name, *args, user=None, **kwargs):
        user = user if user is not None else current_user

        self.plugin_name = plugin_name

        kwargs["key_prefix"] = plugin_name
        kwargs["suffix"] = plugin_name

        super().__init__(*args, user=user, **kwargs)


def run_hook(name, **kwargs):
    r"""Run the plugin hook with the given name for all registered plugins.

    :param name: The name of the hook.
    :param \**kwargs: Additional keyword arguments that will be passed to the hook.
    :return: A single result, if ``firstresult`` is set to ``True`` in the hook spec, or
        a list of results.
    :raises ValueError: If no valid hook with the given name was found.
    """
    hook = getattr(current_app.plugin_manager.hook, name, None)

    if hook is None:
        raise ValueError(f"No valid hook with the name '{name}' was found.")

    return hook(**kwargs)


def template_hook(name, **kwargs):
    r"""Run the plugin hook with the given name inside a template.

    Uses :func:`run_hook` and joins multiple results together as a string ready to be
    inserted into a template.

    :param name: See :func:`run_hook`.
    :param \**kwargs: See :func:`run_hook`.
    :return: The template string, which may be empty if the given hook was not found or
        raised an exception.
    """
    try:
        result = run_hook(name, **kwargs)
    except Exception as e:
        current_app.logger.exception(e)
        result = ""

    if isinstance(result, list):
        result = "\n".join([r if r is not None else "" for r in result])
    elif result is None:
        result = ""

    return Markup(result)


def get_plugin_config(name):
    """Get the configuration of a plugin.

    For each plugin, configuration can be specified by mapping the name of the plugin to
    the configuration that the plugin expects in the ``PLUGIN_CONFIG`` value as
    configured in the application's configuration. Each configuration has to be
    specified as a dictionary.

    :param name: The name of the plugin.
    :return: The plugin configuration or an empty dictionary if no valid configuration
        could be found.
    """
    config = current_app.config["PLUGIN_CONFIG"].get(name, {})

    if not isinstance(config, dict):
        return {}

    return config
