"""Invenio OAuthClient module for AAF (Australian Access Federation)
integration.

This package provides OpenID Connect integration for AAF with InvenioRDM.
"""

from importlib.metadata import version

__version__ = version("invenio-oauthclient-aaf")

from .handlers import account_info
from .remote import (
    AAF_HELPER,
    AAF_REMOTE_APP,
    AAF_SANDBOX_HELPER,
    AAF_SANDBOX_REMOTE_APP,
    REMOTE_APP,
    REMOTE_SANDBOX_APP,
    AAFSettingsHelper,
)

__all__ = (
    "account_info",
    "AAF_REMOTE_APP",
    "REMOTE_APP",
    "AAF_SANDBOX_REMOTE_APP",
    "REMOTE_SANDBOX_APP",
    "AAFSettingsHelper",
    "AAF_HELPER",
    "AAF_SANDBOX_HELPER",
    "__version__",
)
