import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import * as api from '../api/client';

const AuthContext = createContext(null);

function persistSession(data, setToken, setUser) {
  localStorage.setItem('jobshield_token', data.token);
  setToken(data.token);
  setUser(data.user);
  return data;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('jobshield_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await api.me();
        if (!cancelled) setUser(data.user);
      } catch {
        localStorage.removeItem('jobshield_token');
        if (!cancelled) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    boot();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(user && token),
      async login(email, password) {
        const data = await api.login({ email, password });
        return persistSession(data, setToken, setUser);
      },
      async register(name, email, password) {
        // Does not issue a session token — email OTP verification is required next.
        return api.register({ name, email, password });
      },
      async verifyEmail(email, otp) {
        const data = await api.verifyEmail({ email, otp });
        return persistSession(data, setToken, setUser);
      },
      async resendOtp(email) {
        return api.resendOtp({ email });
      },
      async forgotPassword(email) {
        return api.forgotPassword({ email });
      },
      async resetPassword(email, otp, new_password) {
        return api.resetPassword({ email, otp, new_password });
      },
      logout() {
        localStorage.removeItem('jobshield_token');
        setToken(null);
        setUser(null);
      },
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
