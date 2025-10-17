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
from elasticsearch import Elasticsearch as _Elasticsearch
from flask import current_app
from flask import g


class Elasticsearch:
    """Elasticsearch client for use in a Flask application.

    Wraps the official client for ease of use in a Flask application. Requires an
    application context, as it uses the application's configuration value
    ``ELASTICSEARCH_HOSTS`` to specifiy one or more Elasticsearch nodes to connect to
    and optionally ``ELASTICSEARCH_CONFIG`` for any further configuration.

    :param app: (optional) The application object.
    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the application's configuration.

        :param app: The application object.
        """
        app.config.setdefault("ELASTICSEARCH_HOSTS", "http://localhost:9200")
        app.config.setdefault("ELASTICSEARCH_CONFIG", {"timeout": 15})
        app.config.setdefault("ELASTICSEARCH_ENABLE_FALLBACK", False)

    def __getattr__(self, attr):
        if not hasattr(g, "_elasticsearch"):
            hosts = current_app.config["ELASTICSEARCH_HOSTS"]

            if isinstance(hosts, str):
                hosts = [hosts]
            elif not hosts:
                hosts = []

            g._elasticsearch = _Elasticsearch(
                hosts=hosts, **current_app.config["ELASTICSEARCH_CONFIG"]
            )

        return getattr(g._elasticsearch, attr)


es = Elasticsearch()
