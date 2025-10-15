from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests

from ..log import footprint
from .exception import RequestException, exception_to_dict
from .jsonable_encoder import jsonable_encoder


def request(
    method: str,
    path: str,
    host: Optional[str] = None,
    auth_key: Optional[str] = None,
    auth_value: Optional[str] = None,
    auth_type: Optional[str] = None,
    disable_caching: bool = True,
    full_return: bool = False,
    json_return: bool = True,
    internal_service: bool = True,
    add_dt_user_agent: bool = True,
    push_logs: bool = True,
    **kwargs: Any,
) -> Union[requests.Response, Any, str, None]:
    controller = f"{__name__}.request"
    """Send an HTTP request with standardized headers, authentication, and
    error handling.

    Args:
        method: HTTP method (GET, POST, etc.).
        path: Endpoint path relative to host.
        host: Base URL of the service.
        auth_key: Key for authentication header or param.
        auth_value: Value for authentication.
        auth_type: 'headers' or 'params'.
        disable_caching: If True, set no-cache headers.
        full_return: If True, return the raw Response.
        json_return: If True, attempt to parse JSON (unless full_return).
        internal_service: If True, expect JSON with 'success' and 'data'.
        add_dt_user_agent: If True, include DealerTower user-agent.
        push_logs: If True, send errors to footprint.
        **kwargs: Passed directly to requests.request().

    Returns:
        Depending on flags: Response, parsed JSON data, text, or None if host missing.

    Raises:
        RequestException: On network errors or JSON/parsing issues.
    """
    if not host:
        return None

    url = urljoin(host.rstrip("/") + "/", path.lstrip("/"))
    headers: Dict[str, Any] = {}
    params: Dict[str, Any] = {}

    # Merge user-provided headers & params
    if "headers" in kwargs:
        headers.update(jsonable_encoder(kwargs.pop("headers", {}) or {}))
    if "params" in kwargs:
        params.update(kwargs.pop("params", {}) or {})

    # Authentication
    if auth_key and auth_value and auth_type in ("headers", "params"):
        target = headers if auth_type == "headers" else params
        target[auth_key] = auth_value

    # Disable caching headers
    if disable_caching:
        headers.update(
            {
                "Cache-Control": "private, no-cache, no-store, must-revalidate, max-age=0, s-maxage=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )

    # Add default user-agent
    if add_dt_user_agent:
        headers.setdefault("User-Agent", "DealerTower-Service/1.0")

    # Prepare footprint context
    error_context = {
        "subject": "Error sending request",
        "controller": controller,
        "payload": {
            "method": method,
            "url": url,
            "disable_caching": disable_caching,
            "json_return": json_return,
            "internal_service": internal_service,
        },
    }

    try:
        resp = requests.request(method, url, headers=headers, params=params, **kwargs)
        status = resp.status_code
    except Exception as exc:
        if push_logs:
            error_context["payload"]["error"] = exception_to_dict(exc)
            footprint.leave(**error_context, log_type="error", message="Request failed")
        raise RequestException(
            status_code=500,
            controller="dtpyfw.core.request",
            message="Request sending error",
        )

    if full_return:
        return resp

    if not json_return:
        return resp.text

    # Parse JSON
    try:
        body = resp.json()
    except Exception as exc:
        if push_logs:
            error_context["payload"].update(
                {
                    "error": exception_to_dict(exc),
                    "headers": dict(resp.headers),
                    "text": resp.text,
                }
            )
            footprint.leave(
                **error_context, log_type="error", message="Invalid JSON response"
            )
        raise RequestException(
            status_code=500,
            controller="dtpyfw.core.request",
            message="Response parsing error",
        )

    # Handle internal service wrapper
    if internal_service:
        success = isinstance(body, dict) and body.get("success", False)
        if success:
            return body.get("data")
        else:
            if push_logs:
                error_context["payload"].update(
                    {
                        "status_code": status,
                        "response": body,
                    }
                )
                footprint.leave(
                    **error_context,
                    log_type="error",
                    message="Service reported failure",
                )
            raise RequestException(
                status_code=status,
                message=body.get("message"),
                controller="dtpyfw.core.request",
            )

    return body
