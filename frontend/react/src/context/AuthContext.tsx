import { createContext, useContext, useState, type ReactNode } from "react";
import { getStoredAuth, setStoredAuth, type Role } from "../api/client";

interface AuthState {
  role: Role;
  apiKey: string;
  setAuth: (role: Role, apiKey: string) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const stored = getStoredAuth();
  const [role, setRole] = useState<Role>(stored.role);
  const [apiKey, setApiKey] = useState(stored.apiKey);

  const setAuth = (nextRole: Role, nextKey: string) => {
    setRole(nextRole);
    setApiKey(nextKey);
    setStoredAuth(nextRole, nextKey);
  };

  return (
    <AuthContext.Provider value={{ role, apiKey, setAuth }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
