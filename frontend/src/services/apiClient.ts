const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";


function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${API_PREFIX}${path}`;
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
  const response = await fetch(buildApiUrl(path));
  return parseResponse<T>(response);
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
    body: formData,
  });
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
  });
  return parseResponse<T>(response);
}
