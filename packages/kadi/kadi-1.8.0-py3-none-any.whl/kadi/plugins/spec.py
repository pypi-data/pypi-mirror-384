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
from pluggy import HookspecMarker


hookspec = HookspecMarker("kadi")


@hookspec
def kadi_get_about_templates():
    """Hook for collecting templates shown on the about page.

    The contents collected by this hook will be shown below the existing content on the
    about page.
    """


@hookspec
def kadi_get_blueprints():
    """Hook for collecting custom Flask blueprints.

    Each plugin can return a single blueprint or a list of blueprints, which will be
    registered in the application. Each blueprint needs to be an instance of a class
    derived from :class:`.PluginBlueprint`, which works like a regular Flask blueprint.
    The actual blueprint definition may look like the following:

    .. code-block:: python3

        from kadi.lib.plugins.core import PluginBlueprint

        bp = PluginBlueprint(
            "my_plugin",
            __name__,
            url_prefix="/my_plugin",
            template_folder="templates",
            static_folder="static",
        )

    Next to the unique name of the blueprint, which may e.g. correspond to the name of
    the plugin, the optional parameters of this example blueprint specify a custom URL
    prefix, which will also be used for the static URL, a folder for searching HTML
    templates and a folder for static files, respectively.

    Note that since API endpoints are handled a bit differently in the application, the
    existing API blueprint, which uses ``api`` as name and ``/api`` as URL prefix,
    should be preferred for custom API endpoints. An example on how to use it may look
    like the following:

    .. code-block:: python3

        from kadi.lib.api.blueprint import bp
        from kadi.lib.api.core import json_response

        @bp.get("/my_plugin/<my_endpoint>")
        def my_endpoint():
            return json_response(200)
    """


@hookspec
def kadi_get_capabilities():
    """Hook for collecting capabilities of the application.

    A capability can for example be an installed external program or a database
    extension, which may be a requirement for other internal functionality or plugins to
    work.

    Each plugin can return a single string or a list of strings, each string
    representing the respective capability. If the requirements for none of the
    capabilities are met, ``None`` can be returned instead.
    """


@hookspec
def kadi_get_content_security_policies():
    """Hook for collecting custom Content Security Policy configurations.

    Each plugin has to return a single dictionary, mapping the resource type of each
    policy to one or more corresponding CSP directives. If multiple plugins return the
    same resource type, the directives will be merged. In cases where no policies should
    be collected, ``None`` can be returned instead.

    An example dictionary may look like the following:

    .. code-block:: python3

        {
            "frame-src": "https://example.com",
            "img-src": ["'self'", "https://example.com/images/"],
        }
    """


@hookspec(firstresult=True)
def kadi_get_custom_mimetype(file, base_mimetype):
    """Hook for determining a custom MIME type of a file.

    Each plugin has to check the given base MIME type and decide whether it should try
    determining a custom MIME type or not. Otherwise, it has to return ``None``. The
    returned MIME type must be based on the content a file actually contains.

    Can be used together with :func:`kadi_get_preview_data`. Note that the hook chain
    will stop after the first returned result that is not ``None``.

    :param file: The :class:`.File` to get the custom MIME type of.
    :param base_mimetype: The base MIME type of the file, based on the actual file
        content, which a plugin can base its decision to return a custom MIME type on.
    """


@hookspec
def kadi_get_index_templates():
    """Hook for collecting templates shown on the index page.

    The contents collected by this hook will be shown below the existing content on the
    index page.

    For simple content, consisting of an image and/or markdown text, the ``INDEX_IMAGE``
    and ``INDEX_TEXT`` configuration values may also be used instead.
    """


@hookspec
def kadi_get_licenses():
    """Hook for collecting custom licenses.

    All licenses have to be returned as a dictionary, mapping the unique name of a
    license to another dictionary, containing the title of the license and an optional
    URL further describing it.

    An example dictionary may look like the following:

    .. code-block:: python3

        {
            "my_license": {
                "title": "My license",
                # Specifying an URL is optional, but recommended.
                "url": "https://example.com",
            },
        }

    Before any custom licenses can be used, they have to be added to the database. This
    can be done using the Kadi CLI, which also allows updating and/or deleting licenses
    that have been added previously:

    .. code-block:: bash

        kadi db licenses --help
    """


@hookspec
def kadi_get_nav_footer_items():
    """Hook for collecting templates for navigation items shown in the footer.

    The contents collected by this hook will be shown on all pages in the footer next to
    the existing navigation items.

    For simple navigation items, without the need for custom styling or translations,
    the ``NAV_FOOTER_ITEMS`` configuration value may also be used instead.
    """


@hookspec
def kadi_get_oauth2_providers():
    """Hook for collecting OAuth2 providers.

    Either a single OAuth2 provider or a list of providers can be returned by each
    plugin. Each provider has to be specified as a dictionary containing all necessary
    information about it, but at least the unique name that was also used to register
    it via :func:`kadi_register_oauth2_providers`.

    An example dictionary may look like the following:

    .. code-block:: python3

        {
            "name": "my_plugin",
            "title": "My Provider",
            "website": "https://example.com",
            "description": "The description of the OAuth2 provider.",
        }

    Needs to be used together with :func:`kadi_register_oauth2_providers`.
    """


@hookspec
def kadi_get_preferences_config():
    """Hook for collecting configuration needed for plugin-specific preferences.

    Plugin preferences are shown in a separate tab on the user's preferences page and
    will be handled by the main application automatically. A plugin can retrieve them
    later on using :func:`kadi.lib.config.core.get_user_config`.

    For adding a custom preferences tab, a plugin has to return a dictionary containing
    a title, form and a callable returning a template (so it can be rendered at
    runtime). The form needs to be an instance of a class derived from
    :class:`.PluginConfigForm` containing the name of the plugin, while the template
    returned by the callable should only contain the rendering of the form fields, since
    the surrounding form element, including the CSRF input field and the submit button,
    are added automatically.

    An example may look like the following:

    .. code-block:: python3

        from flask import render_template
        from kadi.lib.forms import StringField
        from kadi.lib.plugins.core import PluginConfigForm

        class MyPluginForm(PluginConfigForm):
            my_field = StringField("My field")

        @hookimpl
        def kadi_get_preferences_config():
            form = MyPluginForm("my_plugin")
            return {
                "title": "My Plugin",
                "form": form,
                "get_template": lambda: render_template(
                    "my_plugin/preferences.html", form=form
                ),
            }
    """


@hookspec(firstresult=True)
def kadi_get_preview_data(file):
    """Hook for obtaining preview data of a file to be passed to the frontend.

    Each plugin has to check whether preview data should be returned for the given file,
    based on e.g. its storage type, size or MIME types, otherwise it has to return
    ``None``. The preview data must consist of a tuple containing the preview type and
    the actual preview data used for rendering the preview later on.

    Should be used together with :func:`kadi_get_preview_templates` and
    :func:`kadi_get_scripts`. Note that the hook chain will stop after the first
    returned result that is not ``None``.

    :param file: The :class:`.File` to get the preview data of.
    """


@hookspec
def kadi_get_preview_templates(file):
    """Hook for collecting templates for rendering preview data.

    Each template should consist of an HTML snippet containing all necessary markup to
    render the preview data. As currently all previews are rendered using Vue.js
    components, the easiest way to include a custom preview is by using such a
    component, which can automatically receive the preview data from the backend as
    shown in the following example:

    .. code-block:: html

        <!-- Check the preview type first before rendering the component. -->
        <div v-if="previewData.type === 'my_preview_type'">
            <!-- Pass the preview data from the backend into the component. -->
            <my-preview-component :data="previewData.data"></my-preview-component>
        </div>

    In order to actually register the custom component via JavaScript,
    :func:`kadi_get_scripts` can be used. Should also be used together with
    :func:`kadi_get_preview_data`.

    :param file: The :class:`.File` to get the preview of.
    """


@hookspec(firstresult=True)
def kadi_get_publication_form(provider, resource):
    """Hook for collecting a publication form of a specific provider.

    Each plugin has to check the given provider and type of the given resource to decide
    whether it should return a form or not, otherwise it has to return ``None``. The
    returned form should be be an instance of a class derived from :class:`.BaseForm`.

    After successful validation, the data obtained via the form will be passed into the
    :func:`kadi_publish_resource` hook as ``form_data``, where it may be used to further
    customize the publication process.

    Needs to be used together with :func:`kadi_get_publication_form_template` and
    :func:`kadi_publish_resource`. Note that the hook chain will stop after the first
    returned result that is not ``None``.

    :param provider: The unique name of the publication provider.
    :param resource: The :class:`.Record` or :class:`.Collection` that will be
        published.
    """


@hookspec(firstresult=True)
def kadi_get_publication_form_template(provider, resource, form):
    """Hook for collecting a publication form template of a specific provider.

    Each plugin has to check the given provider and type of the given resource to decide
    whether it should return a form template or not, otherwise it has to return
    ``None``. The template should only contain the rendering of the form fields, since
    the surrounding form element, including the CSRF input field and the submit button,
    will be added automatically.

    Needs to be used together with :func:`kadi_get_publication_form_template` and
    :func:`kadi_publish_resource`. Note that the hook chain will stop after the first
    returned result that is not ``None``.

    :param provider: The unique name of the publication provider.
    :param resource: The :class:`.Record` or :class:`.Collection` that will be
        published.
    :param form: The form object as returned by :func:`kadi_get_publication_form`.
    """


@hookspec
def kadi_get_publication_providers(resource):
    """Hook for collecting publication providers.

    Either a single publication provider or a list of providers can be returned by each
    plugin. Each provider has to be specified as a dictionary containing all necessary
    information about it, but at least the unique name that was also used to register
    the OAuth2 provider that this publication provider should use. The given resource
    can be used to adjust the returned information based on the resource type.

    An example dictionary may look like the following:

    .. code-block:: python3

        {
            "name": "my_plugin",
            "description": "The (HTML) description of the publication provider.",
        }

    Needs to be used together with :func:`kadi_register_oauth2_providers` and
    :func:`kadi_get_oauth2_providers`.

    :param resource: The :class:`.Record` or :class:`.Collection` that is targeted for
        publication.
    """


@hookspec(firstresult=True)
def kadi_get_default_rate_limit():
    """Hook for determining a custom default rate limit.

    The returned rate limit must be a string according to the specification of the
    `Flask-Limiter <https://flask-limiter.readthedocs.io>`__ library. Different limits
    may be returned depending on e.g. the current endpoint (retrieved via the
    ``endpoint`` attribute of ``flask.request``) or other requirements. Returning an
    empty string will disable the rate limit altogether.

    Note that this hook will not be called for the static file endpoint and for
    endpoints that already have a fixed rate limit applied. Also note that the hook
    chain will stop after the first returned result that is not ``None``. If no plugin
    returns a valid result, the configured default rate limits will be used instead.
    """


@hookspec
def kadi_get_resource_overview_templates(resource):
    """Hook for collecting templates shown on the overview pages of resources.

    The contents collected by this hook will be shown below the existing actions and
    links on the respective resource overview page. For resource types where no
    templates should be collected, ``None`` can be returned instead.

    :param resource: The resource which the overview page belongs to, either a
        :class:`.Record`, :class:`.File`, :class:`.Collection`, :class:`.Template` or
        :class:`.Group`.
    """


@hookspec
def kadi_get_scripts():
    """Hook for collecting JavaScript sources.

    Each plugin can return a single string or a list of strings, each string
    representing the full URL where the script can be loaded from. As only internal
    scripts can currently be used, scripts should be loaded via a custom static route,
    which a plugin can define by using :func:`kadi_get_blueprints`.

    Note that by default, the scripts are inserted on every page. Plugins may limit each
    script to certain pages based on e.g. the current endpoint (retrieved via the
    ``endpoint`` attribute of ``flask.request``) or other requirements. In cases where
    no script should be inserted, the plugin has to return ``None``.

    An example of using this hook could be the registration of a custom, global Vue.js 3
    component (using the options API), which can be used in combination with a template
    such as the one shown in :func:`kadi_get_preview_templates`:

    .. code-block:: js

        // Register the component in the main app.
        kadi.app.component('my-preview-component', {
            // The data to preview. Its type depends on how the preview data is returned
            // from the backend.
            props: {
                data: String,
            },
            // Note the custom delimiters, which are used so they can coexist with
            // Jinja's templating syntax when not using single file components like in
            // this case.
            template: `
                <div>{$ data $}</div>
            `,
        })
    """


@hookspec
def kadi_get_storage_providers():
    """Hook for collecting storage providers.

    Either a single storage provider or a list of storage providers can be returned by
    each plugin. Each storage provider must be an instance of a class derived from
    :class:`.BaseStorage` with a unique storage type.

    In cases where no storage provider should be collected, ``None`` can be returned
    instead.
    """


@hookspec
def kadi_get_background_tasks():
    """Hook for collecting background tasks to be run via Celery.

    Either a single or a list of multiple tasks can be returned by each plugin. Each
    returned task must be a reference to a corresponding task function.

    A definition of an example task function may look like the following:

    .. code-block:: python3

        from kadi.ext.celery import celery

        @celery.task(name="my_plugin.my_task")
        def _my_plugin_task(**kwargs):
            pass

    Registered tasks can be triggered by name using
    :func:`kadi.lib.tasks.core.launch_task` or by implementing
    :func:`kadi_get_background_task_schedules`.
    """


@hookspec(firstresult=True)
def kadi_get_background_task_notification(task):
    """Hook for collecting notification data related to a background task.

    The notification data has to be returned as a tuple containing the title and the
    (HTML) body of the notification. Each of these components may also be ``None``, in
    which case a fallback value will be determined automatically depending on the state
    of the task. If a certain task should be ignored, e.g. based on its name, ``None``
    can be returned instead.

    Note that this hook will only be triggered for tasks that are kept in the database
    and for which notifications have been enabled. See also the parameters of
    :func:`kadi.lib.tasks.core.launch_task`.

    Needs to be used together with :func:`kadi_get_background_tasks`. Note that the
    hook chain will stop after the first returned result that is not ``None``.

    :param task: The :class:`.Task` object for which corresponding notification data
        should be collected.
    """


@hookspec
def kadi_get_background_task_schedules():
    """Hook for collecting background task schedules.

    Schedules can be used to periodically run background tasks defined using
    :func:`kadi_get_background_tasks`. The returned schedule must be a dictionary
    according to the periodic task specification of `Celery
    <https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html>`__.

    A definition of an example schedule of a task with no arguments that should run
    every 30 seconds may look like the following:

    .. code-block:: python3

        {
            "my-plugin-task": {
                "task": "my_plugin.my_periodic_task",
                "schedule": 30,
            },
        }
    """


@hookspec(firstresult=True)
def kadi_get_terms(query, page, per_page):
    """Hook for collecting term IRIs and related information from terminology services.

    The terms have to be returned as a tuple, containing the total number of terms
    corresponding to the given search query as well as the terms themselves. The latter
    have to consist of a list of dictionaries, each dictionary containing at least the
    term IRI and an optional HTML body.

    An example dictionary may look like the following:

    .. code-block:: python3

        {
            "term": "https://example.org#example_term",
            # If no body is specified, the term will be used as default content.
            "body": '<a href="https://example.org#example_term">Example Term</a>',
        }

    In order to inform the main application about a term search being provided by a
    plugin, the ``"term_search"`` capability has to be returned using
    :func:`kadi_get_capabilities`.

    Note that the hook chain will stop after the first returned result that is not
    ``None``.

    :param query: The search query, which may be an empty string.
    :param page: The current result page used for pagination, starting at ``1``.
    :param per_page: The number of results per page used for pagination.
    """


@hookspec
def kadi_get_translations_bundles(locale):
    """Hook for collecting translation bundles used for frontend translations.

    Each plugin has to return a single translation bundle consisting of a dictionary
    that maps the strings to translate to their corresponding translated values
    according to the given locale. This dictionary may also be constructed by e.g.
    loading an external JSON file, containing the actual translations.

    If a certain locale should be ignored, ``None`` can be returned instead. The same
    can be done to limit the translations to certain pages based on e.g. the current
    endpoint (retrieved via the ``endpoint`` attribute of ``flask.request``) or other
    requirements.

    The translations can then be used in the frontend by calling the globally available
    ``$t`` function with the corresponding text to translate:

    .. code-block:: js

        const translatedText = $t('My translated text');

    This can be combined with custom scripts registered via
    :func:`kadi_get_scripts`, including the use within custom Vue.js components.

    Note that the texts to translate will themselves be used as a fallback if no
    corresponding translation can be found. Therefore, it is recommended to keep these
    texts in english, like in the example above, as english is used as the default
    locale in the application and will therefore need no further handling. Also note
    that translations of the main application always take precedence.

    For adding custom backend translations, please see
    :func:`kadi_get_translations_paths`.

    :param locale: The locale for which translations are collected, currently one of
        ``"en"`` or ``"de"``.
    """


@hookspec
def kadi_get_translations_paths():
    """Hook for collecting translations paths used for backend translations.

    Each plugin has to return a single translations path, which must be absolute and
    needs to contain a configuration file called ``babel.cfg``, as required by the
    `Flask-Babel <https://python-babel.github.io/flask-babel>`__ library in order to
    find and extract strings to translate. Afterwards, the Kadi CLI can be used to
    initialize or update all message catalogs for the desired languages, for example:

    .. code-block:: bash

        kadi i18n --help

    As this process is similar to how translations in the main application are handled,
    please see the developer documentation for more information. Note that translations
    of the main application currently always take precedence.

    For adding custom frontend translations, please see
    :func:`kadi_get_translations_bundles`.
    """


@hookspec
def kadi_post_app_initialization(app):
    """Hook to perform additional initializations during application startup.

    This hook allows plugins to perform additional initializations during application
    startup. Specifically, the hook is run directly after all other initializations have
    been completed, including configuration handling and the registration of Flask
    extensions and background tasks.

    :param app: The Flask application instance which can be used to perform all
        necessary initializations.
    """


@hookspec
def kadi_post_resource_change(revision):
    """Hook to run operations after a resource was created or changed.

    This hook is only executed after all changes have been persisted in the database and
    if the creation or change triggered the creation of a new revision of the respective
    resource. The given revision can be used to react to specific changes, e.g. based on
    the revisioned resource (``revision.object``), the user that triggered the revision
    (``revision.user``) or whether a parent revision (``revision.parent``) exists, i.e.
    whether the resources was newly created or changed instead.

    :param revision: The revision that was created after a resource was created or
        changed. Supported resources are instances of :class:`.Record`, :class:`.File`,
        :class:`.Collection`, :class:`.Template` or :class:`.Group`.
    """


@hookspec(firstresult=True)
def kadi_publish_resource(provider, resource, form_data, user, client, token, task):
    """Hook for publishing a resource using a specific provider.

    Each plugin has to check the given provider and decide whether it should start the
    publishing process, otherwise it has to return ``None``. After finishing the
    publishing process, the plugin has to return a tuple consisting of a flag indicating
    whether the operation succeeded and a (HTML) template further describing the result
    in a user-readable manner, e.g. containing a link to view the published result if
    the operation was successful.

    Needs to be used together with :func:`kadi_get_publication_providers`. Note that the
    hook chain will stop after the first returned result that is not ``None``.

    :param provider: The unique name of the publication provider.
    :param resource: The :class:`.Record` or :class:`.Collection` to publish.
    :param form_data: Form data as dictionary to customize the publication process, see
        :func:`kadi_get_publication_form`. Note that the dictionary will be empty if a
        plugin does not specify a custom form.
    :param user: The :class:`.User` who started the publication process.
    :param client: The OAuth2 client to use for authenticated requests together with the
        token.
    :param token: The OAuth2 client token in a format usable by the client.
    :param task: A :class:`.Task` object that may be provided if this hook is executed
        in a background task. Can be used to check whether the publishing operation was
        canceled and to update the current progress of the operation via the task.
    """


@hookspec
def kadi_register_oauth2_providers(registry):
    """Hook for registering OAuth2 providers.

    Currently, only the authorization code grant type is supported. Each provider needs
    to register itself to the given registry provided by the `Authlib
    <https://docs.authlib.org>`__ library using a unique name, e.g. corresponding to the
    name of the plugin.

    Needs to be used together with :func:`kadi_get_oauth2_providers`.

    :param registry: The OAuth2 provider registry, which is used to register the
        provider via its ``register`` method.
    """
