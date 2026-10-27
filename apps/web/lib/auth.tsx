"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

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
    // Check localStorage on mount
    // Wrapped in setTimeout to avoid MetaMask extension interference
    const timer = setTimeout(() => {
      try {
        const savedToken = localStorage.getItem("tripsense_token");
        const savedUser = localStorage.getItem("tripsense_user");
        if (savedToken && savedUser) {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
        }
      } catch (e) {
        // Silently handle errors from browser extensions
        if (!(e instanceof Error && e.message.includes("addListener"))) {
          console.warn("Could not read auth state from storage", e);
        }
      }
    }, 0);
    
    return () => clearTimeout(timer);
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
