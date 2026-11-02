import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "@/lib/auth";

function AuthStatus() {
  const { isAuthenticated, user } = useAuth();
  return <div>{isAuthenticated ? user?.email : "signed-out"}</div>;
}

describe("auth session restoration", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("removes an invalid saved session instead of presenting it as authenticated", async () => {
    localStorage.setItem("tripsense_token", "stale-token");
    localStorage.setItem("tripsense_user", JSON.stringify({ id: "u1", email: "traveler@example.com" }));
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ detail: "Could not validate credentials" }), { status: 401 }))),
    );

    render(
      <AuthProvider>
        <AuthStatus />
      </AuthProvider>,
    );

    await waitFor(() => expect(localStorage.getItem("tripsense_token")).toBeNull());
    expect(screen.getByText("signed-out")).toBeInTheDocument();
  });

  it("validates and normalizes a saved bearer token before restoring the session", async () => {
    localStorage.setItem("tripsense_token", "Bearer valid-token");
    localStorage.setItem("tripsense_user", JSON.stringify({ id: "u1", email: "cached@example.com" }));
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ id: "u1", email: "verified@example.com" }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      ),
    );

    render(
      <AuthProvider>
        <AuthStatus />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("verified@example.com")).toBeInTheDocument());
    expect(localStorage.getItem("tripsense_token")).toBe("valid-token");
  });
});
