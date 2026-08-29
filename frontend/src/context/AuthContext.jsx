import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { fetchMe, loginUser, registerUser } from "../lib/api";

const AuthContext = createContext(null);

const TOKEN_KEY = "horizon_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      setInitializing(false);
      return;
    }
    fetchMe()
      .then((u) => !cancelled && setUser(u))
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
        }
      })
      .finally(() => !cancelled && setInitializing(false));
    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (email, password) => {
    const { access_token } = await loginUser(email, password);
    localStorage.setItem(TOKEN_KEY, access_token);
    setToken(access_token);
    const me = await fetchMe();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (email, password) => {
    await registerUser(email, password);
    return login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, user, initializing, isAuthed: !!token, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
