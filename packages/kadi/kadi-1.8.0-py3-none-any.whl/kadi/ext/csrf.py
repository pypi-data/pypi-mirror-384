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
from flask import current_app
from flask import request
from flask_wtf.csrf import CSRFProtect


class KadiCSRFProtect(CSRFProtect):
    """Custom CSRF protection extension."""

    def _get_csrf_token(self):
        # Check the headers before the form to prevent the full read of the input stream
        # when the CSRF token can already be found here.
        for header_name in current_app.config["WTF_CSRF_HEADERS"]:
            csrf_token = request.headers.get(header_name)

            if csrf_token:
                return csrf_token

        field_name = current_app.config["WTF_CSRF_FIELD_NAME"]
        base_token = request.form.get(field_name)

        if base_token:
            return base_token

        for key in request.form:
            if key.endswith(field_name):
                csrf_token = request.form[key]

                if csrf_token:
                    return csrf_token

        return None


csrf = KadiCSRFProtect()
