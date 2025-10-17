# Copyright 2025 Karlsruhe Institute of Technology
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

import base64
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from authlib.oidc.core import UserInfo
from cryptography.hazmat.primitives import serialization
from flask import current_app

from kadi.lib.oauth.models import OAuth2ServerAuthCode


def oidc_enabled():
    """Check if OpenID-Connect is enabled.

    :returns: True if the everything is configured to use OIDC, False otherwise.
    """
    return bool(current_app.config["OIDC_SIGNING_KEYS"])


def get_oidc_scopes():
    """Get all available OpenID Connect scopes."""
    return {"oidc": ["openid", "profile", "email"]}


def get_oidc_scopes_if_enabled():
    """Get all available OpenID Connect scopes if OIDC is configured."""
    return get_oidc_scopes() if oidc_enabled() else {}


def contains_oidc_scopes(scopes):
    """Check whether the scopes contain an OpenID Connect scope."""
    return "oidc." in scopes


def normalize_oidc_scopes(scopes):
    """Transform the OIDC scopes from the Kadi notation to the official notation."""
    normalized_scopes = []

    for scope in scopes.split():
        parts = scope.split(".", 1)

        if "oidc" in parts[0]:
            normalized_scopes.append(parts[1])
        else:
            normalized_scopes.append(scope)

    return " ".join(normalized_scopes)


def get_issuer():
    """Returns the issuer of the ID token.

    :returns: The issuer.
    """
    url_scheme = current_app.config["PREFERRED_URL_SCHEME"]
    server_name = current_app.config["SERVER_NAME"]

    return f"{url_scheme}://{server_name}"


def is_nonce_used(client_id, nonce):
    """Checks if a nonce is currently used by a client.

    :param client_id: The OAuth2 client ID.
    :param nonce: The nonce used for a OAuth2 request.
    :return ``True`` if the nonce is currently used by a client, ``False`` otherwise.
    """
    if not nonce:
        return False

    exists = OAuth2ServerAuthCode.query.filter_by(
        client_id=client_id, nonce=nonce
    ).first()

    return bool(exists)


def generate_user_info(user, scope):
    """Maps the Kadi user to an OIDC user info.
    :returns: The OIDC user info.
    """
    return UserInfo(
        sub=str(user.id),
        name=user.identity.username,
        email=user.identity.email,
        email_verified=user.identity.email_confirmed,
        preferred_username=user.displayname,
    ).filter(scope)


@lru_cache(maxsize=16)
def _load_signing_key_from_cache(path, mtime_ns):
    """Load a signing key from file and caches it.

    Uses the path and mtime as cache keys.

    :param path: The path to the signing key.
    :param mtime_ns: Modified timestamp of the file.

    :returns: The signing key.
    """
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _load_signing_key(path):
    """Loads a signing key.

    :params path: Path to the key.

    :returns: The key.
    """
    mtime_ns = Path(path).stat().st_mtime_ns
    return _load_signing_key_from_cache(path, mtime_ns)


def get_active_signing_key():
    """Get the active signing key used for ID tokens.

    :returns: The key or None if no key is available.
    """
    signing_keys = current_app.config["OIDC_SIGNING_KEYS"]

    if not signing_keys:
        return None

    return _load_signing_key(signing_keys[0])


def _to_b64(n):
    """Converts a number used in cryptography to base64 url encoded string without
    padding.

    :param n: The number.

    :returns: The encoded string without padding.
    """
    byte_size = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(byte_size)).decode("utf-8").rstrip("=")


def jwk_thumbprint_rsa(rsa_public_key):
    """Generates the JSON Web Key (JWK) thumbprint according to RFC-7638."""
    numbers = rsa_public_key.public_numbers()
    jwk = {
        "kty": "RSA",
        "n": _to_b64(numbers.n),
        "e": _to_b64(numbers.e),
    }

    canonical_jwk = json.dumps(
        {k: jwk[k] for k in sorted(jwk.keys())}, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")

    thumbprint = hashlib.sha256(canonical_jwk).digest()
    return base64.urlsafe_b64encode(thumbprint).rstrip(b"=").decode("utf-8")


def get_jwks():
    """Get the JSON Web Key Set.

    These are the public keys used to verify a ID token.

    :returns: The jwks.
    """
    signing_keys = current_app.config["OIDC_SIGNING_KEYS"]

    jwks = []

    for signing_key in signing_keys:
        private_key = _load_signing_key(signing_key)
        public_key = private_key.public_key()

        numbers = public_key.public_numbers()

        jwks.append(
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": jwk_thumbprint_rsa(public_key),
                "n": _to_b64(numbers.n),
                "e": _to_b64(numbers.e),
            }
        )

    return {"keys": jwks}
