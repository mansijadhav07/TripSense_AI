"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { fetchCurrentUser, normalizeAccessToken } from "./auth-api";

export interface User {
  id: string;
  email: string;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const clearStoredSession = () => {
      localStorage.removeItem("tripsense_token");
      localStorage.removeItem("tripsense_user");
      if (active) {
        setToken(null);
        setUser(null);
      }
    };

    const handleExpiredSession = () => clearStoredSession();
    window.addEventListener("tripsense:auth-expired", handleExpiredSession);

    const restoreSession = async () => {
      try {
        const savedToken = localStorage.getItem("tripsense_token");
        const savedUser = localStorage.getItem("tripsense_user");
        if (!savedToken || !savedUser) {
          clearStoredSession();
          return;
        }

        const normalizedToken = normalizeAccessToken(savedToken);
        let cachedUser: User;
        try {
          cachedUser = JSON.parse(savedUser) as User;
        } catch {
          clearStoredSession();
          return;
        }
        if (!normalizedToken || !cachedUser?.email) {
          clearStoredSession();
          return;
        }

        try {
          const currentUser = await fetchCurrentUser(normalizedToken);
          if (!currentUser) {
            clearStoredSession();
            return;
          }
          if (active) {
            setToken(normalizedToken);
            setUser(currentUser);
            localStorage.setItem("tripsense_token", normalizedToken);
            localStorage.setItem("tripsense_user", JSON.stringify(currentUser));
          }
        } catch (error) {
          console.warn("Could not verify the saved session; retaining it until the API is reachable.", error);
          if (active) {
            setToken(normalizedToken);
            setUser(cachedUser);
          }
        }
      } catch (error) {
        console.warn("Could not restore authentication from browser storage.", error);
      }
    };

    void restoreSession();
    return () => {
      active = false;
      window.removeEventListener("tripsense:auth-expired", handleExpiredSession);
    };
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    try {
      localStorage.setItem("tripsense_token", newToken);
      localStorage.setItem("tripsense_user", JSON.stringify(newUser));
    } catch (e) {
      console.warn("Could not persist auth state", e);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    try {
      localStorage.removeItem("tripsense_token");
      localStorage.removeItem("tripsense_user");
    } catch (e) {
      console.warn("Could not clear auth state", e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
