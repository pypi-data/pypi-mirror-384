"""Tests for AAF OAuth handlers."""

from unittest.mock import Mock

import pytest

from invenio_oauthclient_aaf.handlers import account_info, account_setup


class TestAccountInfo:
    """Test account_info handler."""

    # pylint: disable=unused-argument
    def test_account_info_success(self, app_context):
        """Test successful user info retrieval."""
        # Mock remote and response
        remote = Mock()
        resp = {"access_token": "test_token_123"}

        # Mock the userinfo response
        mock_user_info_response = Mock()
        mock_user_info_response.data = {
            "sub": "user123",
            "email": "test@example.edu.au",
            "name": "Test User",
            "preferred_username": "testuser",
        }
        remote.get.return_value = mock_user_info_response

        # Call the handler
        result = account_info(remote, resp)

        # Assertions
        assert result["user"]["email"] == "test@example.edu.au"
        assert result["user"]["profile"]["full_name"] == "Test User"
        assert result["user"]["profile"]["username"] == "testuser"
        assert result["external_id"] == "user123"
        assert result["external_method"] == "aaf"

        # Verify the correct endpoint was called
        remote.get.assert_called_once_with("https://central.aaf.edu.au/oidc/userinfo")

    def test_account_info_no_access_token(self):
        """Test handling of missing access token."""
        remote = Mock()
        resp = {}  # No access token

        with pytest.raises(Exception, match="No access token received from AAF"):
            account_info(remote, resp)

    # pylint: disable=unused-argument
    def test_account_info_no_email(self, app_context):
        """Test handling of missing email in user info."""
        remote = Mock()
        resp = {"access_token": "test_token_123"}

        mock_user_info_response = Mock()
        mock_user_info_response.data = {
            "sub": "user123",
            "name": "Test User",
            # Missing email
        }
        remote.get.return_value = mock_user_info_response

        with pytest.raises(Exception, match="AAF did not provide user email"):
            account_info(remote, resp)

    # pylint: disable=unused-argument
    def test_account_info_no_sub(self, app_context):
        """Test handling of missing sub (user ID) in user info."""
        remote = Mock()
        resp = {"access_token": "test_token_123"}

        mock_user_info_response = Mock()
        mock_user_info_response.data = {
            "email": "test@example.edu.au",
            "name": "Test User",
            # Missing sub
        }
        remote.get.return_value = mock_user_info_response

        with pytest.raises(Exception, match="AAF did not provide user ID"):
            account_info(remote, resp)

    # pylint: disable=unused-argument
    def test_account_info_username_fallback(self, app_context):
        """Test username fallback when preferred_username is missing."""
        remote = Mock()
        resp = {"access_token": "test_token_123"}

        mock_user_info_response = Mock()
        mock_user_info_response.data = {
            "sub": "user123",
            "email": "test@example.edu.au",
            "name": "Test User",
            # No preferred_username
        }
        remote.get.return_value = mock_user_info_response

        result = account_info(remote, resp)

        # Should use email prefix as username
        assert result["user"]["profile"]["username"] == "test"

    # pylint: disable=unused-argument
    def test_account_info_empty_name(self, app_context):
        """Test handling of empty name field."""
        remote = Mock()
        resp = {"access_token": "test_token_123"}

        mock_user_info_response = Mock()
        mock_user_info_response.data = {
            "sub": "user123",
            "email": "test@example.edu.au",
            "name": "",
            "preferred_username": "testuser",
        }
        remote.get.return_value = mock_user_info_response

        result = account_info(remote, resp)

        assert result["user"]["profile"]["full_name"] == ""

    # pylint: disable=unused-argument
    def test_account_info_api_error(self, app_context):
        """Test handling of AAF API errors."""
        remote = Mock()
        resp = {"access_token": "test_token_123"}

        # Simulate API error
        remote.get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            account_info(remote, resp)


class TestAccountSetup:  # pylint: disable=too-few-public-methods
    """Test account_setup handler."""

    def test_account_setup(self):
        """Test account_setup handler does nothing."""
        remote = Mock()
        token = Mock()
        resp = {"access_token": "test_token"}

        # Should not raise any errors (function returns None)
        account_setup(remote, token, resp)
