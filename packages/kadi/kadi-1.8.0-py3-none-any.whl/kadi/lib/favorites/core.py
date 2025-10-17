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
from flask_login import current_user

from kadi.ext.db import db

from .models import Favorite


def is_favorite(object_name, object_id, user=None):
    """Check if the given object is favorited by the given user.

    :param object_name: The type of object.
    :param object_id: The ID of the object.
    :param user: (optional) The user the favorite belongs to. Defaults to the current
        user.
    :return: ``True`` if the object is favorited, ``False`` otherwise.
    """
    user = user if user is not None else current_user

    favorite = (
        user.favorites.filter(
            Favorite.object == object_name, Favorite.object_id == object_id
        )
        .with_entities(Favorite.id)
        .first()
    )
    return favorite is not None


def toggle_favorite(object_name, object_id, user=None):
    """Toggle the favorite state of the given object for the given user.

    If a favorite already exists for the given object and user, it will be deleted from
    the database, otherwise it will be created.

    :param object_name: The type of object.
    :param object_id: The ID of the object.
    :param user: (optional) The user the favorite belongs to. Defaults to the current
        user.
    """
    user = user if user is not None else current_user

    favorite = user.favorites.filter(
        Favorite.object == object_name, Favorite.object_id == object_id
    ).first()

    if favorite is not None:
        db.session.delete(favorite)
    else:
        Favorite.create(user=user, object=object_name, object_id=object_id)


def delete_favorites(object_name, object_id):
    """Delete all favorites of the given object.

    :param object_name: The type of object.
    :param object_id: The ID of the object.
    """
    favorites = Favorite.query.filter(
        Favorite.object == object_name, Favorite.object_id == object_id
    )

    for favorite in favorites:
        db.session.delete(favorite)
