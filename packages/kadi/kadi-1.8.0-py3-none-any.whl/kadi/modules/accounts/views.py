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
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask_babel import format_number
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.ext.limiter import limiter
from kadi.lib.db import update_object
from kadi.lib.format import filesize
from kadi.lib.mails.utils import send_email_confirmation_mail
from kadi.lib.mails.utils import send_password_reset_mail
from kadi.lib.utils import utcnow
from kadi.lib.web import flash_danger
from kadi.lib.web import flash_success
from kadi.lib.web import get_next_url
from kadi.lib.web import html_error_response
from kadi.lib.web import url_for
from kadi.modules.accounts.providers.oidc import OIDCProvider
from kadi.modules.collections.models import Collection
from kadi.modules.collections.models import CollectionState
from kadi.modules.groups.models import Group
from kadi.modules.groups.models import GroupState
from kadi.modules.records.models import File
from kadi.modules.records.models import FileState
from kadi.modules.records.models import Record
from kadi.modules.records.models import RecordState
from kadi.modules.sysadmin.utils import legals_acceptance_required
from kadi.modules.templates.models import Template
from kadi.modules.templates.models import TemplateState

from .blueprint import bp
from .forms import EmailConfirmationForm
from .forms import LegalsAcceptanceForm
from .forms import PasswordResetForm
from .forms import RegisterLocalUserForm
from .forms import RegisterOIDCUserForm
from .forms import RequestPasswordResetForm
from .forms import get_login_form
from .models import Identity
from .models import LocalIdentity
from .models import User
from .models import UserState
from .providers import LDAPProvider
from .providers import LocalProvider
from .providers import ShibProvider
from .utils import decode_email_confirmation_token
from .utils import decode_password_reset_token
from .utils import login_user
from .utils import logout_user


@bp.get("/login")
def login():
    """Page to select an authentication provider to log in with.

    See :func:`login_with_provider`.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    auth_providers = list(current_app.config["AUTH_PROVIDERS"])
    forms = []

    for auth_provider in auth_providers:
        form = get_login_form(auth_provider)
        forms.append(form)

    return render_template(
        "accounts/login.html",
        title=_("Login"),
        forms=forms,
        js_context={"auth_providers": auth_providers},
    )


@bp.route("/login/<provider>", methods=["GET", "POST"])
@limiter.limit("5/minute")
@limiter.limit("50/minute", key_func=lambda: "login_with_provider")
def login_with_provider(provider):
    """Page to log in with a specific authentication provider."""
    if (
        current_user.is_authenticated
        or provider not in current_app.config["AUTH_PROVIDERS"]
    ):
        return redirect(url_for("main.index"))

    form = get_login_form(provider)

    if provider == const.AUTH_PROVIDER_TYPE_LOCAL:
        return _login_local(provider, form)

    if provider == const.AUTH_PROVIDER_TYPE_LDAP:
        return _login_ldap(provider, form)

    if provider == const.AUTH_PROVIDER_TYPE_OIDC:
        return _login_oidc(provider, form)

    if provider == const.AUTH_PROVIDER_TYPE_SHIB:
        return _login_shib(provider, form)

    return html_error_response(404)


def _login_local(provider, form):
    fallback_url = url_for("accounts.login", tab=provider)

    if request.method == "GET":
        return redirect(fallback_url)

    if form.validate():
        user_info = LocalProvider.authenticate(
            username=form.username.data, password=form.password.data
        )

        if user_info.is_authenticated:
            identity = user_info.data

            login_user(identity)
            db.session.commit()

            return redirect(get_next_url())

    flash_danger(_("Invalid credentials."))
    return redirect(fallback_url)


def _login_ldap(provider, form):
    fallback_url = url_for("accounts.login", tab=provider)

    if request.method == "GET":
        return redirect(fallback_url)

    if form.validate():
        user_info = LDAPProvider.authenticate(
            username=form.username.data, password=form.password.data
        )

        if user_info.is_authenticated:
            ldap_data = user_info.data
            identity = LDAPProvider.register(
                displayname=ldap_data.displayname,
                username=ldap_data.username,
                email=ldap_data.email,
            )

            if identity:
                login_user(identity)
                db.session.commit()

                return redirect(get_next_url())

            flash_danger(_("Error registering user."))
            return redirect(fallback_url)

    flash_danger(_("Invalid credentials."))
    return redirect(fallback_url)


def _login_oidc(provider, form):
    fallback_url = url_for("accounts.login", tab=provider)

    if request.method == "GET":
        return redirect(fallback_url)

    if form.validate():
        return OIDCProvider.initiate_login(form.oidc_provider.data)

    return redirect(fallback_url)


def _login_shib(provider, form):
    if request.method == "POST":
        if form.validate():
            target = url_for(
                "accounts.login_with_provider", provider=const.AUTH_PROVIDER_TYPE_SHIB
            )
            url = ShibProvider.get_session_initiator(form.idp.data, target)
            return redirect(url)

        flash_danger(_("Invalid Identity Provider."))

    elif request.method == "GET":
        if ShibProvider.contains_valid_idp():
            user_info = ShibProvider.authenticate()

            if user_info.is_authenticated:
                shib_data = user_info.data
                identity = ShibProvider.register(
                    displayname=shib_data.displayname,
                    username=shib_data.username,
                    email=shib_data.email,
                )

                if identity:
                    login_user(identity)
                    db.session.commit()

                    return redirect(get_next_url())

                flash_danger(_("Error registering user."))

            else:
                shib_meta = ShibProvider.get_metadata()
                required_attrs = ShibProvider.get_required_attributes()

                return render_template(
                    "accounts/shib_missing_attributes.html",
                    title=_("Login failed"),
                    sp_entity_id=shib_meta["sp_entity_id"],
                    idp_entity_id=shib_meta["idp_entity_id"],
                    idp_displayname=shib_meta["idp_displayname"],
                    idp_support_contact=shib_meta["idp_support_contact"],
                    required_attrs=required_attrs,
                    timestamp=utcnow().isoformat(),
                )

        else:
            flash_danger(_("Invalid Identity Provider."))
            url = ShibProvider.get_logout_initiator(url_for("accounts.login"))
            return redirect(url)

    return redirect(url_for("accounts.login", tab=provider))


@bp.get("/logout")
def logout():
    """Endpoint to log a user out of the application."""
    return redirect(logout_user())


def _send_email_confirmation_mail(identity, email=None):
    if send_email_confirmation_mail(identity, email=email):
        flash_success(_("A confirmation email has been sent."))
    else:
        flash_danger(_("Could not send confirmation email."))


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3/minute", methods=["POST"])
@limiter.limit(
    "30/minute", methods=["POST"], key_func=lambda: "local_provider_register"
)
def local_provider_register():
    """Page to register a new local user."""
    if not LocalProvider.allow_registration() or current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterLocalUserForm()
    enforce_legals = legals_acceptance_required()

    if not enforce_legals:
        del form.accept_legals

    if request.method == "POST":
        if form.validate():
            identity = LocalProvider.register(
                displayname=form.displayname.data,
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
            )

            if identity:
                if identity.needs_email_confirmation:
                    _send_email_confirmation_mail(identity)

                if enforce_legals:
                    identity.user.accept_legals()
                    db.session.commit()

                flash_success(_("Registration completed successfully."))
                return redirect(
                    url_for("accounts.login", tab=const.AUTH_PROVIDER_TYPE_LOCAL)
                )

        flash_danger(_("Error registering user."))

    return render_template(
        "accounts/register_local.html",
        title=_("Register"),
        form=form,
        enforce_legals=enforce_legals,
    )


@bp.route("/oidc/authorize/<provider>")
def oidc_provider_authorize(provider):
    """Redirect endpoint to handle the OIDC authorization code."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    user_info = OIDCProvider.authenticate(provider=provider)

    if user_info.is_authenticated:
        oidc_data = user_info.data
        identity = OIDCProvider.get_identity(
            issuer=oidc_data.issuer, subject=oidc_data.subject
        )

        if identity:
            login_user(identity)
            db.session.commit()

            return redirect(get_next_url())

        # Store the user information in the session as a dictionary.
        session[const.SESSION_KEY_OIDC_DATA] = oidc_data._asdict()
        return redirect(url_for("accounts.oidc_provider_register"))

    flash_danger(_("Error authenticating user."))
    return redirect(url_for("accounts.login", tab=const.AUTH_PROVIDER_TYPE_OIDC))


@bp.route("/oidc/register", methods=["GET", "POST"])
def oidc_provider_register():
    """Page to register a new OIDC user after authentication."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    oidc_data = session.get(const.SESSION_KEY_OIDC_DATA)

    if oidc_data is None:
        return redirect(url_for("accounts.login", tab=const.AUTH_PROVIDER_TYPE_OIDC))

    form = RegisterOIDCUserForm(data=oidc_data)
    enforce_legals = legals_acceptance_required()

    if not enforce_legals:
        del form.accept_legals

    if request.method == "POST":
        if form.validate():
            email_confirmed = False

            # Only confirm the email directly if it was provided (as confirmed) via OIDC
            # and not changed by the user.
            if oidc_data["email_confirmed"] and oidc_data["email"] == form.email.data:
                email_confirmed = True

            identity = OIDCProvider.register(
                displayname=form.displayname.data,
                username=form.username.data,
                email=form.email.data,
                email_confirmed=email_confirmed,
                issuer=oidc_data["issuer"],
                subject=oidc_data["subject"],
            )

            if identity:
                if identity.needs_email_confirmation:
                    _send_email_confirmation_mail(identity)

                if enforce_legals:
                    identity.user.accept_legals()

                login_user(identity)
                db.session.commit()

                flash_success(_("Registration completed successfully."))
                return redirect(get_next_url())

        flash_danger(_("Error registering user."))

    return render_template(
        "accounts/register_oidc.html",
        title=_("Register"),
        form=form,
        enforce_legals=enforce_legals,
    )


@bp.route("/confirm-email", methods=["GET", "POST"])
@login_required
def request_email_confirmation():
    """Page to request confirmation for a user's email address."""
    identity = current_user.identity

    if not identity.needs_email_confirmation:
        return redirect(url_for("main.index"))

    email = identity.email
    form = EmailConfirmationForm()

    if form.validate_on_submit():
        _send_email_confirmation_mail(identity, email=form.email.data or email)
        return redirect(url_for("accounts.request_email_confirmation"))

    return render_template(
        "accounts/request_email_confirmation.html",
        title=_("Email confirmation"),
        form=form,
        email=email,
    )


@bp.get("/confirm-email/<token>")
@login_required
def confirm_email(token):
    """Page to confirm a user's email address.

    The token to confirm the email address must be a JSON web token obtained via
    :func:`request_email_confirmation`.
    """
    if current_user.identity.email_confirmed:
        return redirect(url_for("main.index"))

    payload = decode_email_confirmation_token(token)

    if not payload:
        flash_danger(_("Token invalid or expired."))
        return redirect(url_for("main.index"))

    identity = Identity.query.get(payload["id"])

    if identity == current_user.identity and not identity.email_confirmed:
        update_object(identity, email=payload["email"], email_confirmed=True)
        db.session.commit()

        flash_success(_("Email confirmed successfully."))

    return redirect(url_for("main.index"))


@bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("2/minute", methods=["POST"])
@limiter.limit("20/minute", methods=["POST"], key_func=lambda: "request_password_reset")
def request_password_reset():
    """Page to request a reset for a local user's password."""
    if not LocalProvider.is_registered() or current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RequestPasswordResetForm()

    if form.validate_on_submit():
        identity = LocalIdentity.query.filter_by(username=form.username.data).first()

        if identity and identity.user is not None:
            send_password_reset_mail(identity)

        # Always indicate success, so anonymous users cannot use this functionality to
        # easily determine existing usernames.
        flash_success(_("A password reset email has been sent."))
        return redirect(url_for("accounts.login", tab=const.AUTH_PROVIDER_TYPE_LOCAL))

    return render_template(
        "accounts/request_password_reset.html", title=_("Password reset"), form=form
    )


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Page to reset a local user's password.

    The token to reset the password must be a JSON web token obtained from
    :func:`request_password_reset`.
    """
    if not LocalProvider.is_registered() or current_user.is_authenticated:
        return redirect(url_for("main.index"))

    payload = decode_password_reset_token(token)

    if not payload:
        flash_danger(_("Token invalid or expired."))
        return redirect(url_for("main.index"))

    form = PasswordResetForm()

    if form.validate_on_submit():
        identity = LocalIdentity.query.get(payload["id"])
        identity.set_password(form.password.data)
        db.session.commit()

        flash_success(_("Password changed successfully."))
        return redirect(url_for("accounts.login", tab=const.AUTH_PROVIDER_TYPE_LOCAL))

    return render_template(
        "accounts/reset_password.html", title=_("Password reset"), form=form
    )


@bp.route("/accept-legals", methods=["GET", "POST"])
@login_required
def request_legals_acceptance():
    """Page to request acceptance of all legal notices."""
    if not current_user.needs_legals_acceptance:
        return redirect(url_for("main.index"))

    form = LegalsAcceptanceForm()

    if form.validate_on_submit():
        current_user.accept_legals()
        db.session.commit()

        return redirect(url_for("main.index"))

    return render_template(
        "accounts/request_legals_acceptance.html",
        title=_("Accept legal notices"),
        form=form,
    )


@bp.get("/inactive-user")
@login_required
def inactive_user():
    """Page to redirect inactive users to."""
    if current_user.state == UserState.ACTIVE:
        return redirect(url_for("main.index"))

    return render_template("accounts/inactive_user.html", title=_("Account inactive"))


@bp.get("/users")
@login_required
def users():
    """User overview page.

    Allows users to filter for users.
    """
    return render_template("accounts/users.html", title=_("Users"))


@bp.get("/users/<int:id>")
@login_required
def view_user(id):
    """Page to view the profile of a user."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return redirect(url_for("accounts.view_user", id=user.new_user_id), code=301)

    return render_template("accounts/view_user.html", user=user, UserState=UserState)


@bp.get("/users/<int:id>/resources")
@login_required
def view_resources(id):
    """Page to view the created and shared resources of a user."""
    user = User.query.get_or_404(id)

    if user.is_merged:
        return redirect(
            url_for("accounts.view_resources", id=user.new_user_id), code=301
        )

    stats = None

    if user == current_user:
        num_records = user.records.filter(
            Record.state == RecordState.ACTIVE,
        ).count()
        num_collections = user.collections.filter(
            Collection.state == CollectionState.ACTIVE,
        ).count()
        num_templates = user.templates.filter(
            Template.state == TemplateState.ACTIVE,
        ).count()
        num_groups = user.groups.filter(
            Group.state == GroupState.ACTIVE,
        ).count()

        files_query = user.files.filter(File.state == FileState.ACTIVE)
        file_size = filesize(
            files_query.with_entities(db.func.sum(File.size)).scalar() or 0
        )

        # Add the user quota information to the formatted file size, if applicable.
        upload_user_quota = current_app.config["UPLOAD_USER_QUOTA"]

        if upload_user_quota is not None:
            file_size += f" / {filesize(upload_user_quota)}"

        stats = {
            "num_records": format_number(num_records),
            "num_collections": format_number(num_collections),
            "num_templates": format_number(num_templates),
            "num_groups": format_number(num_groups),
            "num_files": format_number(files_query.count()),
            "file_size": file_size,
        }

    return render_template(
        "accounts/view_resources.html", title=_("Resources"), user=user, stats=stats
    )


@bp.get("/users/trash")
@login_required
def manage_trash():
    """Page for the current user to manage their deleted resources."""
    return render_template(
        "accounts/manage_trash.html",
        title=_("Trash"),
        user=current_user,
        js_context={"empty_trash_endpoint": url_for("api.empty_trash")},
    )
