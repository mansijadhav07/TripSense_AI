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
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

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
