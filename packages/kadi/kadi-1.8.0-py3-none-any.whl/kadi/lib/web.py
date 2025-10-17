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
import re
import unicodedata
from collections import OrderedDict
from functools import wraps
from io import BytesIO
from mimetypes import guess_type
from urllib.parse import quote
from urllib.parse import urljoin
from urllib.parse import urlparse

from flask import current_app
from flask import flash
from flask import has_request_context
from flask import render_template
from flask import request
from flask import session
from flask import url_for as _url_for
from flask_babel import gettext as _
from werkzeug.datastructures import Headers
from werkzeug.exceptions import default_exceptions
from werkzeug.routing import BaseConverter

import kadi.lib.constants as const
from kadi.lib.cache import memoize_request
from kadi.lib.conversion import parse_boolean_string
from kadi.lib.utils import as_list


URL_RULE_REGEX = re.compile(
    r"""
    (?P<static>[^<]*)                          # Static rule data
    <
    (?:
        (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)  # Converter name
        (?:\((?P<args>.*?)\))?                 # Converter arguments
        \:                                     # Variable delimiter
    )?
    (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)       # Variable name
    >
    """,
    re.VERBOSE,
)


class IdentifierConverter(BaseConverter):
    """Custom URL converter for identifiers.

    Validates arguments according to :func:`kadi.lib.validation.validate_identifier`,
    but also allows and converts/strips uppercase characters and surrounding
    whitespaces.
    """

    regex = r"\s*[a-zA-Z0-9-_]+\s*"

    def to_python(self, value):
        return value.strip().lower()


def flash_danger(message):
    """Flash a danger message to the next request.

    Uses Flask's :func:`flash` function with a fixed ``"danger"`` category.

    :param message: The message to be flashed.
    """
    flash(message, category="danger")


def flash_info(message):
    """Flash an info message to the next request.

    Uses Flask's :func:`flash` function with a fixed ``"info"`` category.

    :param message: The message to be flashed.
    """
    flash(message, category="info")


def flash_success(message):
    """Flash a success message to the next request.

    Uses Flask's :func:`flash` function with a fixed ``"success"`` category.

    :param message: The message to be flashed.
    """
    flash(message, category="success")


def flash_warning(message):
    """Flash a warning message to the next request.

    Uses Flask's :func:`flash` function with a fixed ``"warning"`` category.

    :param message: The message to be flashed.
    """
    flash(message, category="warning")


@memoize_request
def get_locale():
    """Get the current locale.

    The locale will be retrieved from a cookie as defined in
    :const:`kadi.lib.constants.LOCALE_COOKIE_NAME`.

    Supports memoization via :func:`kadi.lib.cache.memoize_request`.

    :return: The current locale. If no valid locale could be found, the default locale
        will be returned.
    """
    default_locale = const.LOCALE_DEFAULT

    if not has_request_context():
        return default_locale

    if const.LOCALE_COOKIE_NAME in request.cookies:
        locale = request.cookies.get(const.LOCALE_COOKIE_NAME)
    else:
        locale = default_locale

    if locale in const.LOCALES:
        return locale

    return default_locale


def get_preferred_locale():
    """Get the preferred locale of the current user's client.

    :return: The preferred locale. If no matching locale could be found, the default
        locale will be returned.
    """
    return request.accept_languages.best_match(
        list(const.LOCALES), default=const.LOCALE_DEFAULT
    )


def encode_filename(filename):
    """Encode a file name for use in a *Content-Disposition* header.

    :param filename: The name of the file to encode.
    :return: A dictionary containing an ASCII version of the file name as ``"filename"``
        and optionally an UTF-8 version as ``"filename*"``.
    """
    try:
        filename.encode("ascii")
    except UnicodeEncodeError:
        # Taken from Werkzeug's "send_file" helper.
        simple_filename = unicodedata.normalize("NFKD", filename)
        simple_filename = simple_filename.encode("ascii", "ignore").decode("ascii")
        quoted_filename = quote(filename, safe="!#$&+-.^_`|~")

        return {
            "filename": simple_filename,
            "filename*": f"UTF-8''{quoted_filename}",
        }

    return {"filename": filename}


def download_bytes(
    data, *, filename, mimetype=None, as_attachment=True, content_length=None
):
    """Send bytes or an iterable of bytes to a client as a file.

    :param data: The binary data to send.
    :param filename: The name of the file to send.
    :param mimetype: (optional) The MIME type of the file to send. Defaults to a MIME
        type based on the given ``filename`` or the default MIME type as defined in
        :const:`kadi.lib.constants.MIMETYPE_BINARY` if it cannot be guessed.
    :param as_attachment: (optional) Whether to send the file as an attachment. Note
        that setting this parameter to ``False`` may pose a security risk, depending on
        the stream contents, client and context.
    :param content_length: (optional) The content length of the data in bytes. If not
        provided, it will be calculated automatically when using bytes or
        :class:`io.BytesIO` and is otherwise omitted in the response.
    :return: The response object.
    """
    headers = Headers()
    headers.set(
        "Content-Disposition",
        "attachment" if as_attachment else "inline",
        **encode_filename(filename),
    )

    if content_length is None:
        if isinstance(data, bytes):
            content_length = len(data)
        elif isinstance(data, BytesIO):
            content_length = data.getbuffer().nbytes

    if content_length is not None:
        headers.set("Content-Length", content_length)

    if mimetype is None:
        mimetype = guess_type(filename)[0] or const.MIMETYPE_BINARY

    return current_app.response_class(
        response=data, mimetype=mimetype, headers=headers, direct_passthrough=True
    )


def url_for(endpoint, _ignore_version=False, **values):
    r"""Generate an URL based on a given endpoint.

    Wraps Flask's ``url_for`` function with additional support for generating the
    correct URLs when using API versioning. Additionally, generated URLs are always
    external, i.e. absolute.

    :param endpoint: The endpoint (name of the function) of the URL.
    :param _ignore_version: (optional) Flag indicating whether the API version should be
        ignored when building the URL in API requests.
    :param \**values: The variable arguments of the URL rule.
    :return: The generated URL string.
    """
    from kadi.lib.api.utils import get_api_version
    from kadi.lib.api.utils import is_api_request

    values["_external"] = True

    if not _ignore_version and is_api_request():
        api_version = get_api_version(default=None)

        if api_version is not None:
            _endpoint = f"{endpoint}_{api_version}"

            # In case the endpoint is not actually versioned, we just fall back to the
            # original one that was passed in.
            try:
                return _url_for(_endpoint, **values)
            except:
                pass

    return _url_for(endpoint, **values)


def static_url(filename):
    """Generate a static URL for a given filename.

    Will make use of the ``MANIFEST_MAPPING`` defined in the application's configuration
    if an entry exists for the given filename.

    :param filename: The name of the file to include in the URL.
    :return: The generated URL string.
    """
    manifest_mapping = current_app.config["MANIFEST_MAPPING"]
    return url_for("static", filename=manifest_mapping.get(filename, filename))


def get_next_url(fallback=None):
    """Get the validated target URL to redirect a user to after login.

    The target URL will be retrieved from the session via
    :const:`kadi.lib.constants.SESSION_KEY_NEXT_URL`.

    :param fallback: (optional) The fallback URL to use in case the target URL is
        invalid or could not be found. Defaults to the index page.
    :return: The validated target URL.
    """
    if has_request_context() and const.SESSION_KEY_NEXT_URL in session:
        next_url = session[const.SESSION_KEY_NEXT_URL]

        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, next_url))

        if test_url.scheme in {"http", "https"} and ref_url.netloc == test_url.netloc:
            return next_url

    return fallback if fallback is not None else url_for("main.index")


def parse_url_rule(rule):
    """Parse an URL rule as used by Werkzeug's internal URL routing.

    Note that this function matches the original URL rule parsing found in
    ``werkzeug.routing.parse_rule`` prior to Werkzeug 2.2.0.

    :param rule: The URL rule to parse.
    :return: A generator of tuples in the form of ``(converter, arguments, variable)``.
    """
    pos = 0
    end = len(rule)
    used_names = set()

    while pos < end:
        m = URL_RULE_REGEX.match(rule, pos)

        if m is None:
            break

        data = m.groupdict()

        if data["static"]:
            yield None, None, data["static"]

        variable = data["variable"]
        converter = data["converter"] or "default"

        if variable in used_names:
            raise ValueError(f"Variable name {variable!r} used twice.")

        used_names.add(variable)
        yield converter, data["args"] or None, variable
        pos = m.end()

    if pos < end:
        remaining = rule[pos:]

        if ">" in remaining or "<" in remaining:
            raise ValueError(f"Malformed url rule: {rule!r}")

        yield None, None, remaining


def get_error_description(status_code):
    """Get an error description corresponding to an HTTP status code.

    :param status_code: The HTTP status code.
    :return: The error description.
    """
    if status_code == 403:
        return _("You do not have permission to access the requested resource.")
    if status_code == 404:
        return _("The requested URL could not be found.")
    if status_code == 429:
        return _("Request limit exceeded, please try again later.")

    exc = default_exceptions.get(status_code)

    if exc is not None:
        return exc.description

    return _("An unknown error occured.")


def html_error_response(status_code, description=None):
    """Return an HTML error response to a client.

    :param status_code: The HTTP status code of the response.
    :param description: (optional) The error description. Defaults to the result of
        :func:`get_error_description` using the given status code.
    :return: The HTML response.
    """
    description = (
        description if description is not None else get_error_description(status_code)
    )

    template = render_template(
        "error.html",
        title=status_code,
        status_code=status_code,
        description=description,
    )
    return current_app.response_class(response=template, status=status_code)


def get_apispec_meta(func):
    """Get the API specification meta dictionary of a view function.

    If not present yet, a corresponding dictionary will be created and set as an
    attribute of the given view function.

    :param func: The view function.
    :return: The newly created or existing meta dictionary.
    """
    if not hasattr(func, const.APISPEC_META_ATTR):
        setattr(func, const.APISPEC_META_ATTR, {})

    return getattr(func, const.APISPEC_META_ATTR)


def qparam(
    name,
    type=const.QPARAM_TYPE_STR,
    multiple=False,
    parse=None,
    default="",
    choice=None,
    description="",
):
    """Decorator to parse a query parameter in a view function.

    Convenience decorator to retrieve and parse a specified query parameter from the
    current request. The decorator can be applied multiple times. Each parameter will be
    injected into the decorated function as part a dictionary inside the keyword
    argument ``qparams``. The dictionary maps each given parameter name to its
    respective value.

    Some information about the query parameter is also used when generating the API
    specification.

    :param name: The name of both the query parameter and the dictionary key that is
        injected into the decorated function.
    :param type: (optional) A string to define the type of the query parameter, which
        also affects its parsing. One of ``string``, ``integer`` or ``boolean``.
    :param multiple: (optional) Flag indicating whether the query parameter can be
        specified multiple times and should be retrieved as list value.
    :param parse: (optional) A callable or list of callables to parse the parameter
        value if it is not missing. Each callable must take and return a single
        parameter value. If parsing fails with a ``ValueError``, the default value is
        taken instead if ``multiple`` is ``False``, otherwise each invalid value is
        removed from the resulting list. Note that the given parsing functions take
        precedence over the default parsing based on the given ``type``.
    :param default: (optional) The default value or a callable returning a default value
        to use in case the query parameter is missing and ``multiple`` is ``False``,
        otherwise the default value will always be an empty list.
    :param choice: (optional) A list of possible parameter values, which is only used
        when generating the API specification.
    :param description: (optional) A description of the query parameter, which is only
        used when generating the API specification. Supports basic Markdown syntax.
    """
    parse = parse if parse is not None else []
    choice = choice if choice is not None else []

    if not parse:
        if type == const.QPARAM_TYPE_INT:
            parse.append(int)
        elif type == const.QPARAM_TYPE_BOOL:
            parse.append(parse_boolean_string)

    def decorator(func):
        # If a callable was provided, it needs to be evaluated each time.
        def _get_default_value(default):
            return default if not callable(default) else default()

        apispec_meta = get_apispec_meta(func)

        qparam_meta = apispec_meta.get(const.APISPEC_QPARAMS_KEY, OrderedDict())
        qparam_meta[name] = {
            "type": type,
            "multiple": multiple,
            "default": _get_default_value(default),
            "choice": choice,
            "description": description,
        }
        qparam_meta.move_to_end(name, last=False)

        if const.APISPEC_QPARAMS_KEY not in apispec_meta:
            apispec_meta[const.APISPEC_QPARAMS_KEY] = qparam_meta

        @wraps(func)
        def wrapper(*args, **kwargs):
            parse_value = True

            if multiple:
                value = request.args.getlist(name)
            else:
                if name in request.args:
                    value = request.args.get(name)
                else:
                    value = _get_default_value(default)
                    # Skip parsing in case we fall back to the default value.
                    parse_value = False

            if parse_value:
                for parse_func in as_list(parse):
                    if multiple:
                        values = []

                        for _value in value:
                            try:
                                values.append(parse_func(_value))
                            except ValueError:
                                pass

                        value = values
                    else:
                        try:
                            value = parse_func(value)
                        except ValueError:
                            value = _get_default_value(default)
                            break

            if "qparams" in kwargs:
                kwargs["qparams"][name] = value
            else:
                kwargs["qparams"] = {name: value}

            return func(*args, **kwargs)

        return wrapper

    return decorator


def paginated(page_max=None, per_page_max=100):
    """Decorator to parse paginated query parameters.

    Convenience decorator to get and parse the query parameters ``"page"`` and
    ``"per_page"`` from the current request. The former defaults to ``1`` while the
    latter defaults to ``10`` if no valid integer values were found. Both parameters
    will be injected into the decorated function as keyword arguments ``page`` and
    ``per_page``.

    The information about the query parameters is also used when generating the API
    specification.

    :param page_max: (optional) The maximum possible value of the ``"page"`` parameter.
    :param per_page_max: (optional) The maximum possible value of the ``"per_page"``
        parameter.
    """

    def decorator(func):
        apispec_meta = get_apispec_meta(func)
        apispec_meta[const.APISPEC_PAGINATION_KEY] = {
            "page_max": page_max,
            "per_page_max": per_page_max,
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            page = request.args.get("page", 1, type=int)
            page = max(page, 1)

            if page_max is not None:
                page = min(page, page_max)

            per_page = request.args.get("per_page", 10, type=int)
            per_page = min(max(per_page, 1), per_page_max)

            kwargs["page"] = page
            kwargs["per_page"] = per_page

            return func(*args, **kwargs)

        return wrapper

    # Decoration without parentheses.
    if callable(page_max) and per_page_max == 100:
        return paginated()(page_max)

    return decorator
