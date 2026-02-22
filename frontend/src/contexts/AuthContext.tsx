import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { User } from "@/types";

// JWT is stored under this key in localStorage
const TOKEN_KEY = "sisimpur_jwt";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  /** Store JWT + user after a successful login / signup (called by SignInPage). */
  login: (token: string, user: User) => void;
  /** Re-fetch the current user from /api/auth/me/ using the stored token. */
  refresh: () => Promise<void>;
  /** Clear local auth state without hitting the server. */
  clearAuth: () => void;
  /** Call /api/auth/logout/ then clear local state. */
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  login: () => {},
  refresh: async () => {},
  clearAuth: () => {},
  signOut: async () => {},
});

/** Read the stored JWT from localStorage (null if not present). */
export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /** Validate the stored token by calling the backend and hydrate user state. */
  const refresh = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const res = await fetch("/api/auth/me/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: User = await res.json();
        setUser(data);
      } else {
        // Token invalid / expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // On mount: validate any existing token
  useEffect(() => {
    refresh();
  }, [refresh]);

  const loginFn = (token: string, userData: User) => {
    localStorage.setItem(TOKEN_KEY, token);
    setUser(userData);
  };

  const clearAuth = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  const signOut = async () => {
    const token = getStoredToken();
    // Best-effort server-side logout (invalidate Supabase session)
    if (token) {
      try {
        await fetch("/api/auth/logout/", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // ignore network errors on logout
      }
    }
    clearAuth();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login: loginFn,
        refresh,
        clearAuth,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

