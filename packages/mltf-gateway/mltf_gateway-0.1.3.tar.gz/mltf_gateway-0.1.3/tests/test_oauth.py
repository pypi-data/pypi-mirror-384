"""
Test suite for OAuth2 client functionality
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mlflow_mltf_gateway.oauth_client import (
    get_stored_credentials,
    store_credentials,
    clear_stored_credentials,
    is_authenticated,
    add_auth_header_to_request,
)


class TestOAuthClient(unittest.TestCase):

    @patch("keyring.get_password")
    def test_get_stored_credentials_no_credentials(self, mock_get_password):
        """Test getting credentials when none are stored"""
        mock_get_password.side_effect = Exception("No credentials found")
        result = get_stored_credentials()
        self.assertIsNone(result)

    @patch("keyring.set_password")
    def test_store_credentials(self, mock_set_password):
        """Test storing credentials"""
        store_credentials("access_token_123", "refresh_token_456", 1234567890)
        # Verify that keyring.set_password was called correctly
        self.assertTrue(mock_set_password.called)

    @patch("keyring.delete_password")
    def test_clear_stored_credentials(self, mock_delete_password):
        """Test clearing stored credentials"""
        clear_stored_credentials()
        # Verify that keyring.delete_password was called correctly
        self.assertTrue(mock_delete_password.called)

    def test_add_auth_header_to_request(self):
        """Test adding auth header to request"""
        # Mock the get_access_token function to return a token
        with patch(
            "mlflow_mltf_gateway.oauth_client.get_access_token"
        ) as mock_get_token:
            mock_get_token.return_value = {"access_token": "test_access_token"}

            headers = {}
            result = add_auth_header_to_request(headers)

            self.assertIn("Authorization", result)
            self.assertEqual(result["Authorization"], "Bearer test_access_token")

    def test_is_authenticated_when_not_authenticated(self):
        """Test is_authenticated when no credentials exist"""
        with patch(
            "mlflow_mltf_gateway.oauth_client.get_stored_credentials"
        ) as mock_get_creds:
            mock_get_creds.return_value = None
            result = is_authenticated()
            self.assertFalse(result)

    def test_is_authenticated_when_authenticated(self):
        """Test is_authenticated when credentials exist but are expired"""
        import time

        with patch(
            "mlflow_mltf_gateway.oauth_client.get_stored_credentials"
        ) as mock_get_creds:
            mock_get_creds.return_value = {
                "access_token": "test_token",
                "expires_at": int(time.time()) - 1000,  # Expired
            }
            result = is_authenticated()
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
