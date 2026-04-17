# Authentication

Petra Vision uses **Microsoft Entra ID** (formerly Azure Active Directory) for authentication. Auth can be disabled for local development.

## Overview

- The **frontend** uses MSAL (Microsoft Authentication Library) to authenticate users via Entra ID
- The **backend** validates Azure AD access tokens on protected endpoints
- Auth is controlled by the `AUTH_ENABLED` environment variable (backend) and `VITE_AUTH_ENABLED` (frontend)

## Disabling Auth for Local Development

Set these in your environment files:

**Backend `.env`:**
```env
AUTH_ENABLED=false
```

**Frontend `.env`:**
```env
VITE_AUTH_ENABLED=false
```

When disabled, the auth gate is bypassed and the backend does not validate tokens.

## Frontend Authentication Flow

The frontend uses `@azure/msal-react` for authentication:

1. **AuthGate** component wraps the entire app
2. If `VITE_AUTH_ENABLED=true`, the user must sign in before accessing any functionality
3. MSAL redirects the user to the Azure Entra login page
4. After successful login, MSAL stores the access token in session storage
5. All API requests include the token in the `Authorization: Bearer {token}` header
6. Token refresh is handled automatically by MSAL

### Frontend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_AUTH_ENABLED` | Enable/disable auth gate | `true` |
| `VITE_AZURE_CLIENT_ID` | Frontend app registration client ID | `fa60a728-...` |
| `VITE_AZURE_TENANT_ID` | Azure AD tenant ID | `dce78d1e-...` |
| `VITE_AZURE_AUTHORITY` | Azure AD authority URL | `https://login.microsoftonline.com/{tenant_id}` |
| `VITE_AZURE_REDIRECT_URI` | Post-login redirect URI | `http://localhost:5173` |
| `VITE_AZURE_POST_LOGOUT_REDIRECT_URI` | Post-logout redirect URI | `http://localhost:5173` |
| `VITE_API_SCOPE` | API scope to request | `api://{client_id}/access_as_user` |

## Backend Token Validation

When `AUTH_ENABLED=true`, the backend validates incoming JWT tokens:

1. Extracts the `Authorization: Bearer {token}` header
2. Fetches the OpenID configuration from Azure to get signing keys
3. Validates the JWT signature, expiry, and structure
4. Checks the token's **audience** matches `AZURE_CLIENT_ID` or `AZURE_AUDIENCE`
5. Checks the **tenant ID** matches `AZURE_TENANT_ID`
6. Checks the **scope** contains `AZURE_REQUIRED_SCOPE`
7. Checks the **client app ID** is in `AZURE_ALLOWED_CLIENT_APP_IDS`
8. Accepts token versions listed in `AZURE_ACCEPTED_TOKEN_VERSIONS`
9. Returns an `AzureUserPrincipal` (subject, tenant, display name, scopes, claims)

Protected routes use the `require_authenticated_principal` dependency from `src/api/deps.py`.

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_ENABLED` | Enable/disable auth | `true` |
| `AZURE_TENANT_ID` | Azure AD tenant ID | Required when auth enabled |
| `AZURE_CLIENT_ID` | Backend app registration client ID | Required when auth enabled |
| `AZURE_AUDIENCE` | Expected token audience | `api://{AZURE_CLIENT_ID}` |
| `AZURE_REQUIRED_SCOPE` | Required scope in the token | `access_as_user` |
| `AZURE_ALLOWED_CLIENT_APP_IDS` | Comma-separated list of allowed client app IDs | Required when auth enabled |
| `AZURE_AUTHORITY_HOST` | Azure authority host | `https://login.microsoftonline.com` |
| `AZURE_ACCEPTED_TOKEN_VERSIONS` | Accepted token versions | `1.0,2.0` |

## Azure App Registrations

You need **two** app registrations in Azure Entra ID:

1. **Backend API** - exposes the `access_as_user` scope
   - Its client ID goes in `AZURE_CLIENT_ID` (backend)
   - Its audience URI goes in `AZURE_AUDIENCE` (e.g., `api://{client_id}`)

2. **Frontend SPA** - configured as a Single Page Application
   - Its client ID goes in `VITE_AZURE_CLIENT_ID` (frontend)
   - Its client ID goes in `AZURE_ALLOWED_CLIENT_APP_IDS` (backend)
   - Redirect URIs: `http://localhost:5173` (dev), your production URL (prod)

The `scripts/entra/sync_apps.py` script can automate app registration setup.

## Key Files

- `src/core/azure_auth.py` - Token validation logic and `AzureUserPrincipal`
- `src/api/deps.py` - Auth dependency injection and route guards
- `frontend/src/auth/config.ts` - MSAL configuration
- `frontend/src/auth/client.ts` - MSAL client setup
- `frontend/src/components/AuthGate/` - Auth gate UI component
