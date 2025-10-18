import json
import msal
import jwt
import time

from ._utils import _load_context

HEADER_PREFIX = "Bearer "


def _check_existing_login() -> bool:
    context, _ = _load_context()
    auth_header = context.get("client_authentication_header_value")
    if not auth_header:
        return False
    token = auth_header.removeprefix(HEADER_PREFIX)
    return _check_valid_token(token)


def _check_valid_token(id_token: str, expiry_headroom_seconds: int = 30) -> bool:
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    exp = decoded.get("exp")
    if not exp:
        return True
    return time.time() + expiry_headroom_seconds < exp


def _obtain_token_from_microsoft_azure(oauth_client_id: str, oauth_authority: str):
    app = msal.PublicClientApplication(oauth_client_id, authority=oauth_authority)
    accounts = app.get_accounts()
    if accounts:
        error_msg = "did not expect multiple Microsoft Azure accounts, this is not yet implemented"
        raise Exception(error_msg)
    else:
        result = app.acquire_token_interactive(scopes=["User.Read", "email"])
    if "id_token" in result:
        return result["id_token"]
    else:
        error_msg = f"""
        failed when attempting to obtain a token from Microsoft Azure
        error: {result.get("error")}
        error_description: {result.get("error_description")}
        correlation_id: {result.get("correlation_id")}
        """
        raise Exception(error_msg)


def _write_token(id_token: str):
    context, context_path = _load_context()
    context["client_authentication_header_value"] = f"{HEADER_PREFIX}{id_token}"
    context["client_authentication_header_name"] = "Authorization"
    with open(context_path, "w") as f:
        json.dump(context, f, indent=4)


def login(allow_existing_token: bool = False):
    context, _ = _load_context()
    oauth_client_id = context.get("oauth_client_id")
    oauth_authority = context.get("oauth_authority")
    if allow_existing_token:
        valid_token = _check_existing_login()
    else:
        valid_token = False
    if valid_token:
        return
    if not oauth_client_id or not oauth_authority:
        error_msg = (
            "context.json must specify both oauth_client_id and oauth_authority keys"
        )
        raise Exception(error_msg)
    id_token = _obtain_token_from_microsoft_azure(oauth_client_id, oauth_authority)
    _write_token(id_token)
