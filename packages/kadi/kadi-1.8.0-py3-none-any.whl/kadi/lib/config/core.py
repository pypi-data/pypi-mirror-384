# Copyright 2021 Karlsruhe Institute of Technology
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
from flask import current_app
from flask import json
from flask_login import current_user

from kadi.config import CONFIG_CLASSES
from kadi.ext.db import db
from kadi.lib.cache import memoize_request
from kadi.lib.db import KadiAesEngine
from kadi.lib.exceptions import KadiDecryptionKeyError
from kadi.lib.utils import compact_json

from .models import ConfigItem


class _Missing:
    def __repr__(self):
        return "<kadi.lib.config.core.MISSING>"

    def __bool__(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


# "Singleton" value that represents a missing config item. Note that this value always
# evaluates to False.
MISSING = _Missing()


@memoize_request
def get_sys_config(key, use_fallback=True):
    """Get the value of a global config item from the database.

    This function can be used as an alternative to directly accessing the application's
    configuration if a certain config item can be stored in the database as well.

    Supports memoization via :func:`kadi.lib.cache.memoize_request`.

    :param key: The key of the config item.
    :param use_fallback: (optional) Whether the application's configuration should be
        used as a fallback if no matching key could be found in the database.
    :return: The value of the config item or a fallback value if no matching item could
        be found and ``use_fallback`` is ``True``, :data:`kadi.lib.config.core.MISSING`
        otherwise.
    """
    config_item = ConfigItem.query.filter(
        ConfigItem.key == key, ConfigItem.user_id.is_(None)
    ).first()

    if config_item is None:
        if use_fallback and key in current_app.config:
            return current_app.config[key]

        return MISSING

    return config_item.value


def set_sys_config(key, value):
    """Set the value of a global config item in the database.

    Note that trying to set an existing config item to its default value, as specified
    in the application's current configuration class, will instead remove this config
    item from the database.

    :param key: The key of the config item.
    :param value: The value of the config item, which needs to be JSON serializable.
    :return: The created or updated config item or ``None`` if either the given key does
        not exist in the application's current configuration class or the given value
        matches the default value of the corresponding key.
    """
    config_cls = CONFIG_CLASSES[current_app.environment]

    for config_key in dir(config_cls):
        # Check if the given key exists at all in the current config class.
        if config_key.isupper() and config_key == key:
            # Check if the given value matches the default value specified in the config
            # class. If so, remove the corresponding config item in the database if it
            # exists, otherwise update or create it.
            if getattr(config_cls, key) == value:
                remove_sys_config(key)
            else:
                return ConfigItem.update_or_create(key=key, value=value)

    return None


def remove_sys_config(key):
    """Remove a global config item from the database.

    :param key: The key of the config item.
    :return: ``True`` if the config item was deleted successfully, ``False`` if no such
        item exists.
    """
    config_items = ConfigItem.query.filter(
        ConfigItem.key == key, ConfigItem.user_id.is_(None)
    ).all()

    if not config_items:
        return False

    # As the uniqueness of global config items is not enforced on the database layer
    # (due to the user ID being NULL), we delete all matching config items here, just in
    # case.
    for config_item in config_items:
        db.session.delete(config_item)

    return True


@memoize_request
def get_user_config(key, user=None, default=MISSING, decrypt=False):
    """Get the value of a user-specific config item from the database.

    Supports memoization via :func:`kadi.lib.cache.memoize_request`.

    :param key: The key of the config item.
    :param user: (optional) The user the config item belongs to. Defaults to the current
        user.
    :param default: (optional) The value to return if no config item was found. Defaults
        to :data:`kadi.lib.config.core.MISSING`.
    :param decrypt: (optional) Flag indicating whether the value of the config item
        should be decrypted.
    :return: The value of the config item or the default value if either no matching
        item could be found or if ``decrypt`` is ``True`` and the value could not be
        decrypted.
    """
    user = user if user is not None else current_user

    config_item = ConfigItem.query.filter(
        ConfigItem.key == key, ConfigItem.user_id == user.id
    ).first()

    if config_item is not None:
        if not decrypt:
            return config_item.value

        try:
            engine = KadiAesEngine.create()
            return json.loads(engine.decrypt(config_item.value))
        except KadiDecryptionKeyError as e:
            current_app.logger.exception(e)

    return default


def set_user_config(key, value, user=None, encrypt=False):
    """Set the value of a user-specific config item in the database.

    :param key: The key of the config item.
    :param value: The value of the config item, which needs to be JSON serializable.
    :param user: (optional) The user the config item belongs to. Defaults to the current
        user.
    :param encrypt: (optional) Flag indicating whether the value of the config item
        should be encrypted.
    :return: The created or updated config item.
    """
    user = user if user is not None else current_user

    if encrypt:
        engine = KadiAesEngine.create()
        value = engine.encrypt(compact_json(value))

    return ConfigItem.update_or_create(key=key, value=value, user=user)


def remove_user_config(key, user=None):
    """Remove a user-specific config item from the database.

    :param key: The key of the config item.
    :param user: (optional) The user the config item belongs to. Defaults to the current
        user.
    :return: ``True`` if the config item was deleted successfully, ``False`` if no such
        item exists.
    """
    user = user if user is not None else current_user

    config_item = ConfigItem.query.filter(
        ConfigItem.key == key, ConfigItem.user_id == user.id
    ).first()

    if not config_item:
        return False

    db.session.delete(config_item)
    return True
