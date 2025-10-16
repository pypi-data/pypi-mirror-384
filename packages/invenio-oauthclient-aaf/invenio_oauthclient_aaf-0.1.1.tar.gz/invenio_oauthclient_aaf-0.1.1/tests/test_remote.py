"""Tests for AAF remote application configuration."""

from invenio_oauthclient_aaf.remote import (
    AAF_HELPER,
    AAF_REMOTE_APP,
    AAF_SANDBOX_HELPER,
    AAF_SANDBOX_REMOTE_APP,
    REMOTE_APP,
    REMOTE_SANDBOX_APP,
    AAFSettingsHelper,
)


class TestAAFSettingsHelper:
    """Test AAFSettingsHelper class."""

    def test_default_initialization(self):
        """Test helper initialization with defaults."""
        helper = AAFSettingsHelper()

        # Access properties from the remote_app
        remote_app = helper.remote_app
        assert remote_app["title"] == "AAF"
        assert remote_app["description"] == ("Connecting Research and Researchers.")
        assert remote_app["params"]["base_url"] == ("https://central.aaf.edu.au/")
        assert remote_app["params"]["app_key"] == "AAF_APP_CREDENTIALS"

    def test_custom_initialization(self):
        """Test helper initialization with custom values."""
        helper = AAFSettingsHelper(
            title="Custom AAF",
            description="Custom Description",
            base_url="https://custom.aaf.edu.au",
            app_key="CUSTOM_CREDENTIALS",
        )

        remote_app = helper.remote_app
        assert remote_app["title"] == "Custom AAF"
        assert remote_app["description"] == "Custom Description"
        assert remote_app["params"]["base_url"] == ("https://custom.aaf.edu.au/")
        assert remote_app["params"]["app_key"] == "CUSTOM_CREDENTIALS"

    def test_url_properties(self):
        """Test URL properties are correctly constructed."""
        helper = AAFSettingsHelper()
        params = helper.remote_app["params"]

        assert params["access_token_url"] == ("https://central.aaf.edu.au/oidc/token")
        assert params["authorize_url"] == ("https://central.aaf.edu.au/oidc/authorize")

    def test_custom_urls(self):
        """Test custom URL override."""
        helper = AAFSettingsHelper(
            access_token_url="https://custom.com/token",
            authorize_url="https://custom.com/authorize",
        )
        params = helper.remote_app["params"]

        assert params["access_token_url"] == "https://custom.com/token"
        assert params["authorize_url"] == "https://custom.com/authorize"

    def test_get_handlers(self):
        """Test get_handlers returns correct structure."""
        helper = AAFSettingsHelper()
        handlers = helper.get_handlers()

        assert "authorized_handler" in handlers
        assert "disconnect_handler" in handlers
        assert "signup_handler" in handlers
        assert handlers["signup_handler"]["info"] == (
            "invenio_oauthclient_aaf.handlers:account_info"
        )
        assert handlers["signup_handler"]["setup"] == (
            "invenio_oauthclient_aaf.handlers:account_setup"
        )

    def test_get_rest_handlers(self):
        """Test get_rest_handlers returns correct structure."""
        helper = AAFSettingsHelper()
        handlers = helper.get_rest_handlers()

        assert "authorized_handler" in handlers
        assert "disconnect_handler" in handlers
        assert "signup_handler" in handlers
        assert "response_handler" in handlers
        assert "authorized_redirect_url" in handlers

    def test_remote_app_property(self):
        """Test remote_app property structure."""
        helper = AAFSettingsHelper()
        # pylint: disable=unsupported-membership-test
        remote_app = helper.remote_app

        assert remote_app["title"] == "AAF"
        assert remote_app["description"] == ("Connecting Research and Researchers.")
        assert "params" in remote_app
        assert "authorized_handler" in remote_app
        assert "signup_handler" in remote_app

    def test_remote_app_params(self):
        """Test remote_app params are correctly set."""
        helper = AAFSettingsHelper()
        params = helper.remote_app["params"]

        assert params["base_url"] == "https://central.aaf.edu.au/"
        assert params["access_token_url"] == ("https://central.aaf.edu.au/oidc/token")
        assert params["authorize_url"] == ("https://central.aaf.edu.au/oidc/authorize")
        assert params["access_token_method"] == "POST"
        assert params["app_key"] == "AAF_APP_CREDENTIALS"
        assert params["request_token_url"] is None
        assert params["content_type"] == "application/json"

    def test_precedence_mask(self):
        """Test precedence_mask is correctly set."""
        helper = AAFSettingsHelper()
        # pylint: disable=unsupported-membership-test
        remote_app = helper.remote_app

        assert "precedence_mask" in remote_app
        assert remote_app["precedence_mask"]["email"] is False

    def test_signup_options(self):
        """Test signup_options are correctly set."""
        helper = AAFSettingsHelper()
        # pylint: disable=unsupported-membership-test
        remote_app = helper.remote_app

        assert "signup_options" in remote_app
        assert remote_app["signup_options"]["auto_confirm"] is True
        assert remote_app["signup_options"]["send_register_msg"] is False

    def test_custom_request_token_params(self):
        """Test custom request token parameters."""
        helper = AAFSettingsHelper(
            request_token_params={
                "scope": "openid profile email custom",
                "prompt": "login",
            }
        )
        params = helper.remote_app["params"]

        assert params["request_token_params"]["scope"] == ("openid profile email custom")
        assert params["request_token_params"]["prompt"] == "login"

    def test_remote_rest_app_property(self):
        """Test remote_rest_app property structure."""
        helper = AAFSettingsHelper()
        # pylint: disable=unsupported-membership-test
        remote_app = helper.remote_rest_app

        assert remote_app["title"] == "AAF"
        assert "params" in remote_app
        assert "authorized_handler" in remote_app
        assert "response_handler" in remote_app


class TestRemoteAppConfiguration:
    """Test exported remote app configurations."""

    def test_aaf_remote_app_structure(self):
        """Test AAF_REMOTE_APP has all required fields."""
        # pylint: disable=unsupported-membership-test
        assert AAF_REMOTE_APP["title"] == "AAF"
        assert AAF_REMOTE_APP["description"] == "Australian Access Federation"
        assert "authorized_handler" in AAF_REMOTE_APP
        assert "disconnect_handler" in AAF_REMOTE_APP
        assert "signup_handler" in AAF_REMOTE_APP
        assert "params" in AAF_REMOTE_APP

    def test_signup_handler_configuration(self):
        """Test signup handler is properly configured."""
        signup_handler = AAF_REMOTE_APP["signup_handler"]

        assert "info" in signup_handler
        assert "setup" in signup_handler
        assert "view" in signup_handler
        assert signup_handler["info"] == ("invenio_oauthclient_aaf.handlers:account_info")
        assert signup_handler["setup"] == ("invenio_oauthclient_aaf.handlers:account_setup")
        assert signup_handler["view"] == ("invenio_oauthclient.handlers:signup_handler")

    def test_params_configuration(self):
        """Test OAuth params are properly configured."""
        params = AAF_REMOTE_APP["params"]

        assert params["request_token_params"] == {"scope": "openid profile email"}
        assert params["base_url"] == "https://central.aaf.edu.au/"
        assert params["access_token_url"] == ("https://central.aaf.edu.au/oidc/token")
        assert params["access_token_method"] == "POST"
        assert params["authorize_url"] == ("https://central.aaf.edu.au/oidc/authorize")
        assert params["app_key"] == "AAF_APP_CREDENTIALS"
        assert params["request_token_url"] is None
        assert params["content_type"] == "application/json"

    def test_remote_app_alias(self):
        """Test REMOTE_APP is an alias for AAF_REMOTE_APP."""
        assert REMOTE_APP is AAF_REMOTE_APP

    def test_sandbox_remote_app_structure(self):
        """Test sandbox remote app configuration."""
        assert AAF_SANDBOX_REMOTE_APP["title"] == "AAF Sandbox"
        assert "Test Environment" in AAF_SANDBOX_REMOTE_APP["description"]

        params = AAF_SANDBOX_REMOTE_APP["params"]
        assert "test.aaf.edu.au" in params["base_url"]
        assert "test.aaf.edu.au" in params["access_token_url"]
        assert "test.aaf.edu.au" in params["authorize_url"]

    def test_sandbox_alias(self):
        """Test REMOTE_SANDBOX_APP is an alias."""
        assert REMOTE_SANDBOX_APP is AAF_SANDBOX_REMOTE_APP

    def test_production_vs_sandbox_urls(self):
        """Test production and sandbox have different URLs."""
        prod_url = AAF_REMOTE_APP["params"]["base_url"]
        sandbox_url = AAF_SANDBOX_REMOTE_APP["params"]["base_url"]

        assert prod_url != sandbox_url
        assert "test" not in prod_url
        assert "test" in sandbox_url

    def test_helpers_exported(self):
        """Test helper instances are exported."""
        assert AAF_HELPER is not None
        assert AAF_SANDBOX_HELPER is not None
        assert isinstance(AAF_HELPER, AAFSettingsHelper)
        assert isinstance(AAF_SANDBOX_HELPER, AAFSettingsHelper)

    def test_helper_base_urls(self):
        """Test helper instances have correct base URLs."""
        assert AAF_HELPER.remote_app["params"]["base_url"] == "https://central.aaf.edu.au/"
        assert (
            AAF_SANDBOX_HELPER.remote_app["params"]["base_url"]
            == "https://central.test.aaf.edu.au/"
        )


class TestHelperExtension:
    """Test extending AAFSettingsHelper."""

    def test_subclass_override_handlers(self):
        """Test subclassing to override handlers."""

        class CustomAAFHelper(AAFSettingsHelper):
            """Custom AAF helper for testing handler overrides."""

            def get_handlers(self):
                handlers = super().get_handlers()
                handlers["signup_handler"]["info"] = "custom.handlers:info"
                return handlers

        helper = CustomAAFHelper()
        handlers = helper.get_handlers()

        assert handlers["signup_handler"]["info"] == ("custom.handlers:info")
        assert helper.remote_app["signup_handler"]["info"] == ("custom.handlers:info")

    def test_subclass_custom_property(self):
        """Test adding custom properties via subclass."""

        class ExtendedAAFHelper(AAFSettingsHelper):
            """Extended AAF helper with custom properties."""

            @property
            def custom_url(self):
                """Return custom URL for testing."""
                base = self.remote_app["params"]["base_url"]
                return f"{base}custom"

        helper = ExtendedAAFHelper()
        assert helper.custom_url == "https://central.aaf.edu.au/custom"
