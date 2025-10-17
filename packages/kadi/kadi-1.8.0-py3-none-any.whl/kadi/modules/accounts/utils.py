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
from uuid import uuid4

from flask import current_app
from flask_login import current_user
from flask_login import login_user as _login_user
from flask_login import logout_user as _logout_user

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import escape_like
from kadi.lib.security import decode_jwt
from kadi.lib.storage.misc import delete_thumbnail
from kadi.lib.storage.misc import save_as_thumbnail
from kadi.lib.utils import compact_json
from kadi.lib.utils import get_class_by_name
from kadi.lib.web import url_for

from .models import User
from .models import UserState
from .providers import ShibProvider
from .schemas import UserSchema


def login_user(identity):
    """Log in a user by their identity.

    Wraps Flask-Login's ``login_user`` function but also ensures that the user's latest
    identity is updated. Note that this function requires an active request context.

    :param identity: The identity to log in with.
    :return: ``True`` if the login was successful, ``False`` otherwise.
    """
    user = identity.user
    user.identity = identity

    return _login_user(user, force=True)


def logout_user():
    """Log out the current user.

    Wraps Flask-Login's ``logout_user`` function. Note that this function requires an
    active request context.

    :return: The URL to redirect the user to after logging out, depending on their
        latest identity.
    """
    redirect_url = url_for("main.index")

    if (
        current_user.is_authenticated
        and current_user.identity is not None
        and current_user.identity.type == const.AUTH_PROVIDER_TYPE_SHIB
        and ShibProvider.is_registered()
    ):
        redirect_url = ShibProvider.get_logout_initiator(redirect_url)

    _logout_user()

    return redirect_url


def save_user_image(user, stream):
    """Save image data as a user's profile image.

    Uses :func:`kadi.lib.storage.misc.save_as_thumbnail` to store the actual image data.
    Note that any previous profile image will be deleted beforehand using
    :func:`delete_user_image`, which will also be called if the image could not be
    saved.

    :param user: The user to set the profile image for.
    :param stream: The image data as a readable binary stream.
    """
    delete_user_image(user)

    user.image_name = uuid4()

    if not save_as_thumbnail(str(user.image_name), stream):
        delete_user_image(user)


def delete_user_image(user):
    """Delete a user's profile image.

    This is the inverse operation of :func:`save_user_image`.

    :param user: The user whose profile image should be deleted.
    """
    if user.image_name:
        delete_thumbnail(str(user.image_name))
        user.image_name = None


def json_user(user):
    """Convert a user into a JSON representation for use in HTML templates.

    :param user: The user to convert.
    :return: The converted user.
    """
    json_data = UserSchema(_internal=True).dump(user)
    return compact_json(json_data, ensure_ascii=True, sort_keys=False)


def _decode_token(token, token_type):
    payload = decode_jwt(token)

    if payload is None or payload.get("type") != token_type:
        return None

    return payload


def decode_email_confirmation_token(token):
    """Decode the given JSON web token used for email confirmation.

    :param token: The token to decode.
    :return: The token's decoded payload or ``None`` if the token is invalid or expired.
    """
    return _decode_token(token, const.JWT_TYPE_EMAIL_CONFIRMATION)


def decode_password_reset_token(token):
    """Decode the given JSON web token used for password resets.

    :param token: The token to decode.
    :return: The token's decoded payload or ``None`` if the token is invalid or expired.
    """
    return _decode_token(token, const.JWT_TYPE_PASSWORD_RESET)


def get_filtered_user_ids(filter_term):
    """Get all IDs of users filtered by the given term.

    Convenience function to filter users based on their displayname and username of
    their latest identity.

    :param filter_term: A (case insensitive) term to filter the users by their display
        name or username.
    :return: The filtered user IDs as query.
    """
    filter_term = escape_like(filter_term)
    user_queries = []

    # Always consider all authentication provider types, not just the currently active
    # ones.
    for provider_type in const.AUTH_PROVIDER_TYPES.values():
        identity_class = get_class_by_name(provider_type["identity"])

        user_query = (
            User.query.join(
                identity_class, identity_class.id == User.latest_identity_id
            )
            .filter(
                db.or_(
                    User.displayname.ilike(f"%{filter_term}%"),
                    identity_class.username.ilike(f"%{filter_term}%"),
                )
            )
            .with_entities(User.id)
        )

        user_queries.append(user_query)

    return user_queries[0].union(*user_queries[1:])


def clean_users(inside_task=False):
    """Clean all deleted users.

    Note that this function may issue one or more database commits.

    :param inside_task: (optional) A flag indicating whether the function is executed in
        a task. In that case, additional information will be logged.
    """
    from .core import purge_user

    users = User.query.filter(User.state == UserState.DELETED)

    if inside_task and users.count() > 0:
        current_app.logger.info(f"Cleaning {users.count()} deleted user(s).")

    for user in users:
        purge_user(user)
