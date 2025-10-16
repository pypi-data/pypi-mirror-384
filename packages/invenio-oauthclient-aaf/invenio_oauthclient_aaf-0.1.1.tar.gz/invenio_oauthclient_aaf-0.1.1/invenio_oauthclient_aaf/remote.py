"""AAF remote application configuration for InvenioRDM OAuth."""

from invenio_oauthclient.contrib.settings import OAuthSettingsHelper


class AAFSettingsHelper(OAuthSettingsHelper):
    """AAF OAuth settings helper."""

    def __init__(
        self,
        title=None,
        description=None,
        base_url=None,
        app_key=None,
        icon=None,
        access_token_url=None,
        authorize_url=None,
        request_token_params=None,
        precedence_mask=None,
        signup_options=None,
    ):
        """Initialize AAF settings helper.

        Args:
            title: Display title for the login button
            description: Description of the authentication provider
            base_url: Base URL for AAF (without trailing slash)
            app_key: Configuration key for credentials
            icon: Icon class/URL for the login button
            access_token_url: Custom access token URL (optional)
            authorize_url: Custom authorize URL (optional)
            logout_url: Logout URL (optional)
            request_token_params: Additional request token parameters
            precedence_mask: Override user input with server data
            signup_options: Auto-confirm and registration message options
        """
        base_url = base_url or "https://central.aaf.edu.au"
        request_token_params = request_token_params or {"scope": "openid profile email"}
        access_token_url = access_token_url or f"{base_url}/oidc/token"
        authorize_url = authorize_url or f"{base_url}/oidc/authorize"
        precedence_mask = precedence_mask or {
            "email": False,
        }
        signup_options = signup_options or {
            "auto_confirm": True,
            "send_register_msg": False,
        }
        icon = icon or "fa fa-university"

        super().__init__(
            title or "AAF",
            description or "Connecting Research and Researchers.",
            base_url,
            app_key or "AAF_APP_CREDENTIALS",
            request_token_params=request_token_params,
            access_token_url=access_token_url,
            authorize_url=authorize_url,
            content_type="application/json",
            precedence_mask=precedence_mask,
            signup_options=signup_options,
            icon=icon,
        )

        # Initialize handlers as instance variables (ORCID pattern)
        self._handlers = {
            "authorized_handler": "invenio_oauthclient.handlers:authorized_signup_handler",
            "disconnect_handler": "invenio_oauthclient.handlers:disconnect_handler",
            "signup_handler": {
                "info": "invenio_oauthclient_aaf.handlers:account_info",
                "setup": "invenio_oauthclient_aaf.handlers:account_setup",
                "view": "invenio_oauthclient.handlers:signup_handler",
            },
        }

        self._rest_handlers = {
            "authorized_handler": "invenio_oauthclient.handlers.rest:authorized_signup_handler",
            "disconnect_handler": "invenio_oauthclient.handlers.rest:disconnect_handler",
            "signup_handler": {
                "info": "invenio_oauthclient_aaf.handlers:account_info",
                "setup": "invenio_oauthclient_aaf.handlers:account_setup",
                "view": "invenio_oauthclient.handlers.rest:signup_handler",
            },
            "response_handler": "invenio_oauthclient.handlers.rest:default_remote_response_handler",
            "authorized_redirect_url": "/",
            "disconnect_redirect_url": "/",
            "signup_redirect_url": "/",
            "error_redirect_url": "/",
        }

    def get_handlers(self):
        """Return AAF handlers."""
        return self._handlers

    def get_rest_handlers(self):
        """Return REST handlers for AAF."""
        return self._rest_handlers


# Default AAF production instance
_aaf_helper = AAFSettingsHelper(
    title="AAF",
    description="Australian Access Federation",
    base_url="https://central.aaf.edu.au",
)

# AAF sandbox/test instance
_aaf_sandbox_helper = AAFSettingsHelper(
    title="AAF Sandbox",
    description="Australian Access Federation (Test Environment)",
    base_url="https://central.test.aaf.edu.au",
)

# Export remote apps (primary exports for users)
AAF_REMOTE_APP = _aaf_helper.remote_app
AAF_SANDBOX_REMOTE_APP = _aaf_sandbox_helper.remote_app

# Aliases for compatibility with InvenioRDM patterns
REMOTE_APP = AAF_REMOTE_APP
REMOTE_SANDBOX_APP = AAF_SANDBOX_REMOTE_APP

# Export helper instances for advanced usage
# (allows accessing URLs, modifying handlers, debugging)
AAF_HELPER = _aaf_helper
AAF_SANDBOX_HELPER = _aaf_sandbox_helper
