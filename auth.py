import os
from functools import wraps

import requests
from flask import request
from jose import jwt


AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
ALGORITHMS = os.environ.get("ALGORITHMS", "RS256").split(",")
API_AUDIENCE = os.environ.get("API_AUDIENCE", "")


class AuthError(Exception):
    """AuthError Exception

    A standardized way to communicate auth failure modes.
    """

    def __init__(self, error, status_code):
        super().__init__()
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header."""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {"code": "authorization_header_missing",
             "description": "Authorization header is expected."},
            401,
        )

    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise AuthError(
            {"code": "invalid_header",
             "description": "Authorization header must start with Bearer."},
            401,
        )
    if len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found."}, 401)
    if len(parts) > 2:
        raise AuthError(
            {"code": "invalid_header",
             "description": "Authorization header must be Bearer token."},
            401,
        )

    return parts[1]


def check_permissions(permission, payload):
    """Check that the required permission is in the JWT payload."""
    permissions = payload.get("permissions", [])
    if not isinstance(permissions, list):
        raise AuthError(
            {"code": "invalid_claims", "description": "Permissions claim must be a list."},
            400,
        )

    if permission not in permissions:
        raise AuthError(
            {"code": "unauthorized", "description": "Permission not found."},
            403,
        )

    return True


def verify_decode_jwt(token):
    """Verify and decode a JWT using Auth0 JWKS."""
    if not AUTH0_DOMAIN or not API_AUDIENCE:
        raise AuthError(
            {"code": "configuration_error",
             "description": "Missing Auth0 config (AUTH0_DOMAIN / API_AUDIENCE)."},
            500,
        )

    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url, timeout=10).json()
    unverified_header = jwt.get_unverified_header(token)

    rsa_key = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key.get("kty"),
                "kid": key.get("kid"),
                "use": key.get("use"),
                "n": key.get("n"),
                "e": key.get("e"),
            }
            break

    if not rsa_key:
        raise AuthError(
            {"code": "invalid_header", "description": "Unable to find the appropriate key."},
            401,
        )

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise AuthError({"code": "token_expired", "description": "Token expired."}, 401) from exc
    except jwt.JWTClaimsError as exc:
        raise AuthError({"code": "invalid_claims", "description": "Incorrect claims."}, 401) from exc
    except Exception as exc:
        raise AuthError({"code": "invalid_token", "description": "Token is invalid."}, 401) from exc


def requires_auth(permission=""):
    """Decorator that enforces JWT auth and RBAC permission."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return decorator
