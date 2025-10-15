"""
Example of OAuth2 Device Flow Authentication using oauthlib

This demonstrates how to implement device flow authentication
with the oauthlib library.
"""

import requests
import time
import webbrowser
from typing import Dict, Any, Optional
from oauthlib.oauth2 import DeviceAuthorizationServer
import json


def authenticate_with_oauthlib_device_flow(
    client_id: str,
    client_secret: str,
    token_url: str,
    authorization_url: str,
    scopes: list = None,
) -> Optional[Dict[str, Any]]:
    """
    Authenticate using OAuth2 device flow with oauthlib

    Args:
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        token_url: Token endpoint URL
        authorization_url: Authorization endpoint URL
        scopes: List of required scopes

    Returns:
        Dictionary containing tokens and metadata or None on failure
    """

    # Prepare the device authorization request
    auth_data = {
        "client_id": client_id,
        "scope": " ".join(scopes) if scopes else "read write",
    }

    try:
        # Request device code from authorization server
        print("Requesting device code...")
        response = requests.post(authorization_url, data=auth_data)
        response.raise_for_status()

        device_info = response.json()
        print(f"Device code: {device_info.get('user_code')}")
        print(f"Verification URL: {device_info.get('verification_uri')}")

        # Open browser for user authorization (optional)
        try:
            webbrowser.open(device_info.get("verification_uri"))
        except Exception as e:
            print(f"Could not open browser: {e}")

        # Poll for access token
        print("Waiting for user authorization...")
        interval = device_info.get("interval", 5)  # polling interval in seconds

        while True:
            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_info.get("device_code"),
            }

            response = requests.post(token_url, data=token_data)

            if response.status_code == 200:
                # Success - we got our tokens
                token_response = response.json()
                print("Authentication successful!")
                return {
                    "access_token": token_response.get("access_token"),
                    "refresh_token": token_response.get("refresh_token"),
                    "expires_in": token_response.get("expires_in"),
                }
            elif response.status_code == 400:
                error_data = response.json()
                error_type = error_data.get("error")

                if error_type == "authorization_pending":
                    print("Waiting for user authorization...")
                    time.sleep(interval)
                    continue
                elif error_type == "slow_down":
                    # Increase polling interval as per spec
                    interval += 5
                    print(f"Slowing down polling, new interval: {interval}s")
                    time.sleep(interval)
                    continue
                else:
                    print(f"Authorization error: {error_data}")
                    return None
            else:
                response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return None


# Example usage with Keycloak configuration
def example_keycloak_authentication():
    """Example using Keycloak configuration"""

    # Configuration for Keycloak instance
    CLIENT_ID = "mltf-gateway-client"
    CLIENT_SECRET = ""  # For public clients, this might be empty
    KEYCLOAK_BASE_URL = "https://keycloak.k8s.accre.vanderbilt.edu/"
    REALM = "mltf-dual-login"

    token_url = f"{KEYCLOAK_BASE_URL}realms/{REALM}/protocol/openid-connect/token"
    auth_url = f"{KEYCLOAK_BASE_URL}realms/{REALM}/protocol/openid-connect/device"

    scopes = ["read", "write"]

    # Perform authentication
    tokens = authenticate_with_oauthlib_device_flow(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_url=token_url,
        authorization_url=auth_url,
        scopes=scopes,
    )

    if tokens:
        print("Access Token:", tokens["access_token"][:50] + "...")
        print("Expires in:", tokens["expires_in"], "seconds")
        return tokens
    else:
        print("Authentication failed!")
        return None


if __name__ == "__main__":
    # Run the example
    example_keycloak_authentication()
