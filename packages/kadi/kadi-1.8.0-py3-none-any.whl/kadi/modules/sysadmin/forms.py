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
from flask_babel import lazy_gettext as _l
from wtforms.validators import DataRequired

from kadi.lib.conversion import empty_str
from kadi.lib.conversion import strip
from kadi.lib.forms import BaseConfigForm
from kadi.lib.forms import BaseForm
from kadi.lib.forms import BooleanField
from kadi.lib.forms import DynamicSelectField
from kadi.lib.forms import FileField
from kadi.lib.forms import JSONField
from kadi.lib.forms import LFTextAreaField
from kadi.lib.forms import SubmitField


class NavFooterField(JSONField):
    """Custom field to process and validate navigation footer items.

    Only performs some basic validation to make sure the overall structure of the items
    is valid.
    """

    def __init__(self, *args, **kwargs):
        kwargs["default"] = []
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            if not isinstance(self.data, list):
                self.data = self.default
                raise ValueError("Invalid data structure.")

            for item in self.data:
                if not isinstance(item, list) or len(item) != 2:
                    self.data = self.default
                    raise ValueError("Invalid data structure.")


class CustomizationConfigForm(BaseConfigForm):
    """A form for use in setting global config items related to customization."""

    broadcast_message = LFTextAreaField(
        _l("Broadcast message"),
        filters=[empty_str, strip],
        description=_l("Shown at the top of all pages to all authenticated users."),
    )

    broadcast_message_public = BooleanField(
        _l("Show broadcast message publicly"),
        description=_l("Show the broadcast message to unauthenticated users as well."),
    )

    nav_footer_items = NavFooterField(
        _l("Navigation footer items"),
        description=_l(
            "Shown on all pages in the footer next to the existing navigation items."
        ),
    )

    index_image = FileField(
        _l("Index image"),
        description=_l("Shown on the index page next to the index text."),
    )

    remove_image = BooleanField(_l("Remove current image"))

    index_text = LFTextAreaField(
        _l("Index text"),
        filters=[empty_str, strip],
        description=_l("Shown on the index page next to the index image."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, ignored_fields={"index_image", "remove_image"}, **kwargs
        )


class LegalsConfigForm(BaseConfigForm):
    """A form for use in setting global config items related to legal notices."""

    terms_of_use = LFTextAreaField(
        _l("Terms of use"),
        filters=[empty_str, strip],
        description=_l(
            "A corresponding shortcut in the navigation footer will be created"
            " automatically."
        ),
    )

    privacy_policy = LFTextAreaField(
        _l("Privacy policy"),
        filters=[empty_str, strip],
        description=_l(
            "A corresponding shortcut in the navigation footer will be created"
            " automatically."
        ),
    )

    enforce_legals = BooleanField(
        _l("Enforce legal notices"),
        description=_l(
            "Require all users to accept the terms of use and/or privacy policy, if at"
            " least one of them is configured."
        ),
    )

    legal_notice = LFTextAreaField(
        _l("Legal notice"),
        filters=[empty_str, strip],
        description=_l(
            "A corresponding shortcut in the navigation footer will be created"
            " automatically."
        ),
    )


class MiscConfigForm(BaseConfigForm):
    """A form for use in setting miscellaneous global config items."""

    robots_noindex = BooleanField(
        _l("Do not index website"),
        description=_l(
            "Exclude this website from being indexed by all major search engines."
        ),
    )


class MergeUsersForm(BaseForm):
    """A form for use in merging users."""

    primary_user = DynamicSelectField(
        _l("Primary user"), coerce=int, validators=[DataRequired()]
    )

    secondary_user = DynamicSelectField(
        _l("Secondary user"), coerce=int, validators=[DataRequired()]
    )

    submit = SubmitField(_l("Merge users"))
