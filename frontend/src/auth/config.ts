import { BrowserCacheLocation, type Configuration, type PopupRequest } from "@azure/msal-browser";


function readRequiredEnv(name: string): string {
  const value = import.meta.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}


export const azureTenantId = readRequiredEnv("VITE_AZURE_TENANT_ID");
export const azureApiScope = readRequiredEnv("VITE_API_SCOPE");
export const azurePostLogoutRedirectUri =
  import.meta.env.VITE_AZURE_POST_LOGOUT_REDIRECT_URI || window.location.origin;

export const msalConfig: Configuration = {
  auth: {
    clientId: readRequiredEnv("VITE_AZURE_CLIENT_ID"),
    authority: import.meta.env.VITE_AZURE_AUTHORITY || `https://login.microsoftonline.com/${azureTenantId}`,
    redirectUri: import.meta.env.VITE_AZURE_REDIRECT_URI || window.location.origin,
    postLogoutRedirectUri: azurePostLogoutRedirectUri,
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: BrowserCacheLocation.SessionStorage,
  },
};

export const loginRequest: PopupRequest = {
  scopes: ["openid", "profile", "email", azureApiScope],
  prompt: "select_account",
};

export const apiTokenRequest: PopupRequest = {
  scopes: [azureApiScope],
};
