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
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import StopValidation

from kadi.lib.conversion import lower
from kadi.lib.conversion import normalize
from kadi.lib.conversion import strip
from kadi.lib.forms import BaseForm
from kadi.lib.forms import BooleanField
from kadi.lib.forms import PasswordField
from kadi.lib.forms import SelectField
from kadi.lib.forms import StringField
from kadi.lib.forms import SubmitField
from kadi.lib.forms import validate_username as _validate_username
from kadi.modules.accounts.models import OIDCIdentity

from .models import Identity
from .models import LocalIdentity
from .models import User
from .providers.oidc import OIDCProvider
from .providers.shib import ShibProvider


def get_login_form(provider):
    """Get a login form based on a given authentication provider.

    All fields and labels will have the given provider appended to their IDs in the form
    of ``"<field_id>_<provider>"``. Additionally, the provider will be saved in the form
    as ``_provider``.

    :param provider: The name of an authentication provider as specificed in
        :const:`kadi.lib.constants.AUTH_PROVIDER_TYPES`.
    :return: The login form.
    """
    form = None
    auth_providers = current_app.config["AUTH_PROVIDERS"]

    if provider in auth_providers:
        form = auth_providers[provider]["form_class"](suffix=provider)
        # Save the provider on the form so it can easily be referenced later on.
        form._provider = provider

    return form


class CredentialsLoginForm(BaseForm):
    """A general login form using a username and a password."""

    username = StringField(
        _l("Username"), filters=[lower, strip], validators=[DataRequired()]
    )

    password = PasswordField(_l("Password"), validators=[DataRequired()])

    submit = SubmitField(_l("Login"))


class OIDCLoginForm(BaseForm):
    """A login form for use in OpenID Connect (OIDC).

    Note that the actual provider validation needs to happen outside this form, as the
    form is simply a container to pass along a selected OIDC provider.
    """

    oidc_provider = StringField(validators=[DataRequired()])

    @property
    def oidc_providers(self):
        """Get a list of all configured OIDC providers.

        See also :meth:`.OIDCProvider.get_providers`.
        """
        return OIDCProvider.get_providers()


class ShibLoginForm(BaseForm):
    """A login form for use in Shibboleth.

    The form uses a selection field which has to be populated with the entity IDs and
    display names of all valid identity providers.
    """

    idp = SelectField(
        _l("Institution"), choices=ShibProvider.get_choices, validators=[DataRequired()]
    )

    submit = SubmitField(_l("Login"))


class BaseUserForm(BaseForm):
    """Base form class for use in creating new users."""

    displayname = StringField(
        _l("Display name"),
        filters=[normalize],
        validators=[
            DataRequired(),
            Length(max=User.Meta.check_constraints["displayname"]["length"]["max"]),
        ],
        description=_l("The display name may be changed later on."),
    )

    username = StringField(
        _l("Username"),
        filters=[lower, strip],
        validators=[
            DataRequired(),
            Length(
                min=Identity.Meta.common_constraints["username"]["length"]["min"],
                max=Identity.Meta.common_constraints["username"]["length"]["max"],
            ),
            _validate_username,
        ],
        description=_l(
            "The username needs to be unique and cannot be changed later on. Valid are"
            " alphanumeric characters with single hyphens or underscores in between."
        ),
    )

    email = StringField(
        _l("Email"),
        filters=[strip],
        validators=[
            DataRequired(),
            Email(),
            Length(max=Identity.Meta.common_constraints["email"]["length"]["max"]),
        ],
    )

    submit = SubmitField(_l("Register"))


class CreateLocalUserForm(BaseUserForm):
    """A form for use in creating new local users."""

    def validate_username(self, field):
        # pylint: disable=missing-function-docstring
        identity = LocalIdentity.query.filter_by(username=field.data).first()

        if identity is not None:
            raise StopValidation(_("Username is already in use."))


class RegisterLocalUserForm(CreateLocalUserForm):
    """A form for use in registering new local users."""

    password = PasswordField(_l("Password"), validators=[DataRequired(), Length(min=8)])

    password2 = PasswordField(
        _l("Repeat password"),
        validators=[DataRequired(), EqualTo("password", _l("Passwords do not match."))],
    )

    accept_legals = BooleanField(validators=[DataRequired()])


class RegisterOIDCUserForm(BaseUserForm):
    """A form for use in registering new OIDC users."""

    accept_legals = BooleanField(validators=[DataRequired()])

    def validate_username(self, field):
        # pylint: disable=missing-function-docstring
        identity = OIDCIdentity.query.filter_by(username=field.data).first()

        if identity is not None:
            raise StopValidation(_("Username is already in use."))


class EmailConfirmationForm(BaseForm):
    """A form for use in mandatory email confirmation."""

    email = StringField(
        _l("Wrong email address? Enter your new email address here:"),
        filters=[strip],
        validators=[
            Optional(),
            Email(),
            Length(max=Identity.Meta.common_constraints["email"]["length"]["max"]),
        ],
    )

    submit = SubmitField(_l("Resend"))


class RequestPasswordResetForm(BaseForm):
    """A form for use in requesting a password reset for local users."""

    username = StringField(
        _l("Username"), filters=[lower, strip], validators=[DataRequired()]
    )

    submit = SubmitField(_l("Submit request"))


class PasswordResetForm(BaseForm):
    """A form for use in changing the password of local users."""

    password = PasswordField(_l("Password"), validators=[DataRequired(), Length(min=8)])

    password2 = PasswordField(
        _l("Repeat password"),
        validators=[DataRequired(), EqualTo("password", _l("Passwords do not match."))],
    )

    submit = SubmitField(_l("Save new password"))


class LegalsAcceptanceForm(BaseForm):
    """A form for use in mandatory acceptance of legal notices."""

    accept_legals = BooleanField(validators=[DataRequired()])

    submit = SubmitField(_l("Continue"))
