/**
 * TripSense AI - Authentication API Client
 * 
 * Handles signup, login, and authenticated API requests
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthResponse {
  success: boolean;
  message?: string;
  access_token?: string;
  token_type?: string;
  user?: {
    id: string;
    email: string;
    created_at?: string;
  };
  data?: {
    user?: {
      id: string;
      email: string;
    };
    token?: {
      access_token: string;
      token_type: string;
    };
  };
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  created_at?: string;
}

export function normalizeAccessToken(token: string): string {
  return token.trim().replace(/^Bearer\s+/i, "");
}

export async function signup(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || data.message || "Registration failed");
  }

  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || data.message || "Login failed");
  }

  return data;
}

/**
 * Get authentication headers for authenticated requests
 */
export function getAuthHeaders(token?: string | null): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (token) headers.Authorization = `Bearer ${normalizeAccessToken(token)}`;
  return headers;
}

/**
 * Make authenticated API request
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {},
  token?: string | null
): Promise<Response> {
  const headers = {
    ...getAuthHeaders(token),
    ...(options.headers || {}),
  };

  return fetch(url, {
    ...options,
    headers,
  });
}

export async function fetchCurrentUser(token: string): Promise<AuthenticatedUser | null> {
  const res = await authenticatedFetch(`${API_BASE_URL}/api/v1/auth/me`, {
    cache: "no-store",
  }, token);

  if (res.status === 401 || res.status === 403) return null;
  if (!res.ok) {
    throw new Error(`Could not restore session (${res.status} ${res.statusText}).`);
  }
  return (await res.json()) as AuthenticatedUser;
}

export async function authenticatedApiFetch(
  url: string,
  options: RequestInit = {},
  token?: string | null
): Promise<Response> {
  const headerToken = new Headers(options.headers).get("Authorization")?.replace(/^Bearer\s+/i, "");
  const res = await authenticatedFetch(url, options, token ?? headerToken);
  if (res.status === 401 || res.status === 403) {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("tripsense:auth-expired"));
    }
    throw new Error("Your session has expired. Please sign in again to continue.");
  }
  return res;
}
