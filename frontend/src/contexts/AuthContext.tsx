import {
  createContext,
  type PropsWithChildren,
  useContext,
  useEffect,
  useState,
} from "react";

import { apiClient, getStoredAccessToken, setStoredAccessToken } from "../api/client";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    apiClient
      .get<User>("/users/me")
      .then((response) => setUser(response.data))
      .catch(() => setStoredAccessToken(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string): Promise<void> {
    const { data } = await apiClient.post<{ access_token: string }>("/auth/login", {
      email,
      password,
    });
    setStoredAccessToken(data.access_token);
    const { data: currentUser } = await apiClient.get<User>("/users/me");
    setUser(currentUser);
  }

  function logout(): void {
    setStoredAccessToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
