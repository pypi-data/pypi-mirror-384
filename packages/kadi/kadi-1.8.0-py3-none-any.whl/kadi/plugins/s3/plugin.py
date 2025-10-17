# Copyright 2024 Karlsruhe Institute of Technology
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


# pylint: disable=missing-function-docstring


from kadi.lib.plugins.core import get_plugin_config
from kadi.plugins import hookimpl

from .constants import PLUGIN_NAME
from .core import S3Storage
from .utils import validate_plugin_config


@hookimpl
def kadi_get_content_security_policies():
    plugin_config = get_plugin_config(PLUGIN_NAME)

    if not validate_plugin_config(plugin_config) or not plugin_config.get(
        "use_presigned_urls", True
    ):
        return None

    endpoint_url = plugin_config["endpoint_url"]

    return {
        "default-src": endpoint_url,
        "frame-src": endpoint_url,
        "img-src": endpoint_url,
    }


@hookimpl
def kadi_get_storage_providers():
    plugin_config = get_plugin_config(PLUGIN_NAME)

    if not validate_plugin_config(plugin_config):
        return None

    return S3Storage(
        endpoint_url=plugin_config["endpoint_url"],
        bucket_name=plugin_config["bucket_name"],
        access_key=plugin_config.get("access_key"),
        secret_key=plugin_config.get("secret_key"),
        region_name=plugin_config.get("region_name"),
        signature_version=plugin_config.get("signature_version"),
        use_presigned_urls=plugin_config.get("use_presigned_urls", True),
        presigned_url_expiration=plugin_config.get("presigned_url_expiration", 60),
        config_kwargs=plugin_config.get("config_kwargs", {}),
    )
