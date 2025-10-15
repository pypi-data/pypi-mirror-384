"""
Environment variable loader for PolarionClient kwargs.

Use:
    from polarion_rest_client import PolarionClient, get_env_vars
    pc = PolarionClient(**get_env_vars())
"""

from __future__ import annotations
from typing import Dict, Any
import os

DEFAULT_TIMEOUT: float = 30.0


def get_env_vars(
    *,
    base_url_var: str = "POLARION_URL",
    token_var: str = "POLARION_TOKEN",
    username_var: str = "POLARION_USERNAME",
    password_var: str = "POLARION_PASSWORD",
    token_prefix_var: str = "POLARION_TOKEN_PREFIX",
    verify_ssl_var: str = "POLARION_VERIFY_SSL",
    timeout_var: str = "POLARION_TIMEOUT",
) -> Dict[str, Any]:
    """
    Read configuration from environment variables and return a kwargs dict
    suitable for PolarionClient(**kwargs).

    Recognized env vars:
      POLARION_URL            (required)
      POLARION_TOKEN          (preferred) OR POLARION_USERNAME + POLARION_PASSWORD
      POLARION_TOKEN_PREFIX   (default: 'Bearer')
      POLARION_VERIFY_SSL     ('true'/'false', default: true)
      POLARION_TIMEOUT        (float seconds, default: 30.0)
    """
    base_url = os.environ.get(base_url_var)
    if not base_url:
        raise ValueError(f"{base_url_var} is required")

    token = os.environ.get(token_var)
    username = os.environ.get(username_var)
    password = os.environ.get(password_var)
    token_prefix = os.environ.get(token_prefix_var, "Bearer")

    verify_ssl_str = os.environ.get(verify_ssl_var, "true").strip().lower()
    verify_ssl = verify_ssl_str not in {"0", "false", "no"}

    timeout_s = os.environ.get(timeout_var)
    timeout: float = float(timeout_s) if timeout_s else DEFAULT_TIMEOUT

    out: Dict[str, Any] = {
        "base_url": base_url,
        "timeout": timeout,
        "verify_ssl": verify_ssl,
        "token_prefix": token_prefix,
    }
    if token:
        out["token"] = token
    elif username and password:
        out["username"] = username
        out["password"] = password
    else:
        raise ValueError(
            "get_env_vars(): provide POLARION_TOKEN or POLARION_USERNAME+POLARION_PASSWORD"
        )

    return out
