import {
  EventType,
  InteractionRequiredAuthError,
  PublicClientApplication,
  type AccountInfo,
  type AuthenticationResult,
} from "@azure/msal-browser";

import { apiTokenRequest, loginRequest, msalConfig } from "@/auth/config";


export const msalInstance = new PublicClientApplication(msalConfig);

let initializationPromise: Promise<void> | null = null;

function getPreferredAccount(): AccountInfo | null {
  return msalInstance.getActiveAccount() || msalInstance.getAllAccounts()[0] || null;
}

export function initializeMsal(): Promise<void> {
  if (!initializationPromise) {
    initializationPromise = msalInstance.initialize().then(() => {
      const account = getPreferredAccount();
      if (account) {
        msalInstance.setActiveAccount(account);
      }

      msalInstance.addEventCallback((event) => {
        if (
          event.eventType === EventType.LOGIN_SUCCESS ||
          event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS
        ) {
          const payload = event.payload as AuthenticationResult | null;
          if (payload?.account) {
            msalInstance.setActiveAccount(payload.account);
          }
        }

        if (event.eventType === EventType.LOGOUT_SUCCESS) {
          msalInstance.setActiveAccount(null);
        }
      });
    });
  }

  return initializationPromise;
}

export async function signInWithMicrosoft(): Promise<void> {
  await initializeMsal();
  const response = await msalInstance.loginPopup(loginRequest);
  if (response.account) {
    msalInstance.setActiveAccount(response.account);
  }
}

export async function acquireApiAccessToken(): Promise<string> {
  await initializeMsal();
  const account = getPreferredAccount();
  if (!account) {
    throw new Error("No authenticated Microsoft account is available.");
  }

  try {
    const response = await msalInstance.acquireTokenSilent({
      ...apiTokenRequest,
      account,
    });
    return response.accessToken;
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      const response = await msalInstance.acquireTokenPopup({
        ...apiTokenRequest,
        account,
      });
      if (response.account) {
        msalInstance.setActiveAccount(response.account);
      }
      return response.accessToken;
    }
    throw error;
  }
}
