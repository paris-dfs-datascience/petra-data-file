import { acquireApiAccessToken } from "@/auth/client";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";


function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${API_PREFIX}${path}`;
}


async function buildAuthorizedHeaders(initialHeaders?: HeadersInit): Promise<Headers> {
  const headers = new Headers(initialHeaders);
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${await acquireApiAccessToken()}`);
  return headers;
}


async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  let message = "Request failed.";
  try {
    const payload = (await response.json()) as { error?: { message?: string }; detail?: string };
    message = payload.error?.message || payload.detail || message;
  } catch {
    const text = await response.text();
    message = text || message;
  }

  throw new Error(message);
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    headers: await buildAuthorizedHeaders(),
  });
  return parseResponse<T>(response);
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
    body: formData,
    headers: await buildAuthorizedHeaders(),
  });
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
    headers: await buildAuthorizedHeaders(),
  });
  return parseResponse<T>(response);
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}
