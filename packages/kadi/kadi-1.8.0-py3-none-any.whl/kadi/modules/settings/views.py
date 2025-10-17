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
from flask_babel import gettext as _
from flask_login import current_user
from flask_login import login_required

from kadi.ext.db import db
from kadi.lib.api.models import PersonalToken
from kadi.lib.api.utils import get_access_token_scopes
from kadi.lib.db import update_object
from kadi.lib.mails.utils import send_email_confirmation_mail
from kadi.lib.oauth.core import create_oauth2_client_token
from kadi.lib.oauth.models import OAuth2ServerClient
from kadi.lib.oauth.utils import get_oauth2_client
from kadi.lib.oauth.utils import get_oauth2_client_token
from kadi.lib.oauth.utils import get_oauth2_provider
from kadi.lib.oauth.utils import get_oauth2_providers
from kadi.lib.oauth.utils import has_oauth2_providers
from kadi.lib.oidc.core import contains_oidc_scopes
from kadi.lib.oidc.core import get_oidc_scopes
from kadi.lib.oidc.core import get_oidc_scopes_if_enabled
from kadi.lib.oidc.core import oidc_enabled
from kadi.lib.web import flash_danger
from kadi.lib.web import flash_success
from kadi.lib.web import html_error_response
from kadi.lib.web import qparam
from kadi.lib.web import url_for
from kadi.modules.accounts.providers.core import get_auth_provider
from kadi.modules.accounts.utils import delete_user_image
from kadi.modules.accounts.utils import save_user_image

from .blueprint import bp
from .forms import ChangePasswordForm
from .forms import CustomizationPreferencesForm
from .forms import EditApplicationForm
from .forms import EditProfileForm
from .forms import NewApplicationForm
from .forms import NewPersonalTokenForm
from .utils import get_plugin_preferences_configs


def _send_email_confirmation_mail(identity):
    if send_email_confirmation_mail(identity):
        flash_success(_("A confirmation email has been sent."))
    else:
        flash_danger(_("Could not send confirmation email."))


@bp.route("", methods=["GET", "POST"])
@login_required
@qparam("action")
def edit_profile(qparams):
    """Page for a user to edit their profile."""
    identity = current_user.identity
    auth_provider = get_auth_provider(identity.type)
    form = EditProfileForm(current_user)

    if request.method == "POST":
        if qparams["action"] == "confirm_email":
            if not identity.email_confirmed:
                _send_email_confirmation_mail(identity)
                return redirect(url_for("settings.edit_profile"))

        elif form.validate():
            update_object(
                current_user,
                displayname=form.displayname.data,
                email_is_private=not form.show_email.data,
                orcid=form.orcid.data,
                about=form.about.data,
            )

            if form.remove_image.data:
                delete_user_image(current_user)
            elif form.image.data:
                save_user_image(current_user, request.files[form.image.name])

            if auth_provider.allow_email_change() and identity.email != form.email.data:
                update_object(identity, email=form.email.data, email_confirmed=False)

                if identity.needs_email_confirmation:
                    _send_email_confirmation_mail(identity)

            db.session.commit()

            flash_success(_("Changes saved successfully."))
            return redirect(url_for("settings.edit_profile"))

        else:
            flash_danger(_("Error updating profile."))

    return render_template(
        "settings/edit_profile.html", title=_("Profile"), form=form, identity=identity
    )


@bp.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    """Page for a user to change their password."""
    identity = current_user.identity
    auth_provider = get_auth_provider(identity.type)

    if not auth_provider.allow_password_change():
        return html_error_response(404)

    form = ChangePasswordForm()

    if request.method == "POST":
        if form.validate() and auth_provider.change_password(
            username=identity.username,
            old_password=form.password.data,
            new_password=form.new_password.data,
        ):
            flash_success(_("Password changed successfully."))
            return redirect(url_for("settings.change_password"))

        flash_danger(_("Error changing password."))

    return render_template(
        "settings/change_password.html", title=_("Password"), form=form
    )


@bp.route("/preferences", methods=["GET", "POST"])
@login_required
@qparam("tab", default="customization")
@qparam("plugin")
def manage_preferences(qparams):
    """Page for a user to manage their preferences."""
    save_changes = False
    customization_form = CustomizationPreferencesForm()

    plugin_configs = get_plugin_preferences_configs()
    current_plugin = qparams["plugin"]

    if current_plugin not in plugin_configs and plugin_configs:
        current_plugin = next(iter(plugin_configs))

    if qparams["tab"] == "customization" and customization_form.validate_on_submit():
        save_changes = True
        customization_form.set_config_values()

    elif qparams["tab"] == "plugins" and request.method == "POST":
        plugin_form = plugin_configs.get(current_plugin, {}).get("form")

        if plugin_form is not None:
            if plugin_form.validate():
                save_changes = True
                plugin_form.set_config_values()
            else:
                flash_danger(_("Error changing preferences."))

    if save_changes:
        db.session.commit()
        flash_success(_("Changes saved successfully."))

        endpoint_args = {"tab": qparams["tab"]}

        if qparams["tab"] == "plugins":
            endpoint_args["plugin"] = current_plugin

        return redirect(url_for("settings.manage_preferences", **endpoint_args))

    return render_template(
        "settings/manage_preferences.html",
        title=_("Preferences"),
        customization_form=customization_form,
        plugin_configs=plugin_configs,
        current_plugin=current_plugin,
    )


@bp.route("/personal-tokens", methods=["GET", "POST"])
@login_required
def manage_personal_tokens():
    """Page for a user to manage their personal tokens."""
    new_token = None
    form = NewPersonalTokenForm()

    if request.method == "POST":
        if form.validate():
            new_token = PersonalToken.new_token()

            PersonalToken.create(
                user=current_user,
                name=form.name.data,
                scope=form.scope.data,
                expires_at=form.expires_at.data,
                token=new_token,
            )
            db.session.commit()

            flash_success(_("Access token created successfully."))

            # Redirecting here would also clear the new token value, so we clear the
            # form manually.
            form.clear()
        else:
            flash_danger(_("Error creating access token."))

    return render_template(
        "settings/manage_personal_tokens.html",
        title=_("Access tokens"),
        form=form,
        new_token=new_token,
        js_context={"scopes": get_access_token_scopes()},
    )


@bp.route("/applications", methods=["GET", "POST"])
@login_required
def manage_applications():
    """Page for a user to manage their registered and authorized OAuth2 applications."""
    client_secret = None
    oauth2_server_client = None

    form = NewApplicationForm()

    if request.method == "POST":
        if form.validate():
            client_secret = OAuth2ServerClient.new_client_secret()
            oauth2_server_client = OAuth2ServerClient.create(
                user=current_user,
                client_secret=client_secret,
                client_name=form.client_name.data,
                client_uri=form.client_uri.data,
                redirect_uris=form.redirect_uris.data,
                scope=form.scope.data,
            )
            db.session.commit()

            flash_success(_("Application registered successfully."))

            # Redirecting here would also clear the new client secret value, so we clear
            # the form manually.
            form.clear()
        else:
            flash_danger(_("Error registering application."))

    return render_template(
        "settings/manage_applications.html",
        title=_("Applications"),
        form=form,
        client_secret=client_secret,
        client=oauth2_server_client,
        js_context={"scopes": get_access_token_scopes() | get_oidc_scopes_if_enabled()},
    )


@bp.route("/applications/<int:id>", methods=["GET", "POST"])
@login_required
def edit_application(id):
    """Page to edit an existing OAuth2 application."""
    oauth2_server_client = current_user.oauth2_server_clients.filter(
        OAuth2ServerClient.id == id
    ).first_or_404()

    form = EditApplicationForm(oauth2_server_client)

    if request.method == "POST":
        if form.validate():
            oauth2_server_client.update_client_metadata(
                client_name=form.client_name.data,
                client_uri=form.client_uri.data,
                redirect_uris=form.redirect_uris.data,
                scope=form.scope.data,
            )
            db.session.commit()

            flash_success(_("Changes saved successfully."))
            return redirect(url_for("settings.manage_applications", tab="manage"))

        flash_danger(_("Error editing application."))

    # If an application has been registered with OpenID Connect, the scopes must be
    # deletable even if OIDC is currently disabled.
    oidc_scopes = (
        get_oidc_scopes()
        if oidc_enabled() or contains_oidc_scopes(form.scope.data)
        else {}
    )

    return render_template(
        "settings/edit_application.html",
        title=_("Edit application"),
        form=form,
        application=oauth2_server_client,
        js_context={"scopes": get_access_token_scopes() | oidc_scopes},
    )


@bp.post("/applications/<int:id>/delete")
@login_required
def delete_application(id):
    """Endpoint to delete an existing OAuth2 application."""
    oauth2_server_client = current_user.oauth2_server_clients.filter(
        OAuth2ServerClient.id == id
    ).first_or_404()

    db.session.delete(oauth2_server_client)
    db.session.commit()

    flash_success(_("Application deleted successfully."))
    return redirect(url_for("settings.manage_applications", tab="manage"))


@bp.route("/services", methods=["GET", "POST"])
@login_required
@qparam("disconnect")
def manage_services(qparams):
    """Page for a user to manage their connected OAuth2 services/providers."""
    if not has_oauth2_providers():
        return html_error_response(404)

    if request.method == "POST":
        provider = qparams["disconnect"]
        oauth2_client_token = get_oauth2_client_token(provider)

        if oauth2_client_token is not None:
            db.session.delete(oauth2_client_token)
            db.session.commit()

        flash_success(_("Service disconnected successfully."))
        return redirect(url_for("settings.manage_services"))

    providers = get_oauth2_providers()

    return render_template(
        "settings/manage_services.html",
        title=_("Connected services"),
        providers=providers,
    )


@bp.get("/services/login/<provider>")
@login_required
def oauth2_provider_login(provider):
    """Endpoint to initiate the OAuth2 flow to connect a provider."""
    oauth2_provider = get_oauth2_provider(provider)

    if oauth2_provider is None:
        return html_error_response(404)

    if oauth2_provider["is_connected"]:
        return redirect(url_for("settings.manage_services"))

    redirect_uri = url_for("settings.oauth2_provider_authorize", provider=provider)

    try:
        client = get_oauth2_client(provider)
        return client.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.exception(e)
        flash_danger(_("Error connecting service."))

    return redirect(url_for("settings.manage_services"))


@bp.get("/services/authorize/<provider>")
@login_required
def oauth2_provider_authorize(provider):
    """Redirect endpoint to handle the OAuth2 authorization code."""
    oauth2_provider = get_oauth2_provider(provider)

    if oauth2_provider is None:
        return html_error_response(404)

    if oauth2_provider["is_connected"]:
        return redirect(url_for("settings.manage_services"))

    try:
        token_data = get_oauth2_client(provider).authorize_access_token()
    except Exception as e:
        current_app.logger.exception(e)

        flash_danger(_("Error connecting service."))
        return redirect(url_for("settings.manage_services"))

    create_oauth2_client_token(
        user=current_user,
        name=provider,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_at=token_data.get("expires_at"),
        expires_in=token_data.get("expires_in"),
    )
    db.session.commit()

    flash_success(_("Service connected successfully."))
    return redirect(url_for("settings.manage_services"))
