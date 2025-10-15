# OAuth2 Integration in MLTF Gateway

This document explains how OAuth2 authentication has been integrated into the MLTF Gateway CLI client.

## Overview

The MLTF Gateway now supports OAuth2 device flow authentication to secure access to the gateway services. This implementation follows OAuth2 best practices and securely stores credentials using the system's keyring.

## Implementation Details

### Authentication Flow

1. **Device Flow**: The client initiates an OAuth2 device flow authentication
2. **User Authorization**: User visits the provided URL and authorizes the application
3. **Token Retrieval**: Client polls for access token until user completes authorization
4. **Credential Storage**: Access and refresh tokens are securely stored using keyring

### Key Components

- `oauth_client.py`: Main OAuth2 implementation with device flow support
- `backend_adapter.py`: Modified to add authentication headers to all REST requests
- CLI integration in `scripts/__init__.py`: Added login/logout commands and authentication checks

## Environment Configuration

The following environment variables can be used to configure the OAuth2 settings:

```bash
MLTF_CLIENT_ID="your_client_id"
MLTF_CLIENT_SECRET="your_client_secret" 
MLTF_AUTH_URL="https://your-oauth-provider.com/oauth/authorize"
MLTF_TOKEN_URL="https://your-oauth-provider.com/oauth/token"
MLTF_SCOPES="read write"
```

## Usage

### Login
```bash
mltf login
```

### Using Commands (requires authentication)
```bash
mltf list
mltf create --name "my-job"
mltf delete --id "job-id"
```

### Logout
```bash
mltf logout
```

## Security Considerations

- Tokens are stored securely using the system's keyring
- Refresh tokens are used to obtain new access tokens automatically
- Access tokens are automatically refreshed when they expire
- All requests to the gateway include proper authentication headers

## Testing

The OAuth2 implementation can be tested by running:
```bash
python oauth_test.py
```

This will demonstrate the complete authentication flow with simulated OAuth2 endpoints.