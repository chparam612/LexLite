import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, AuthContextType } from '../types/auth';
import { apiClient, authApi } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUserProfile = async (authToken: string) => {
    try {
      setIsLoading(true);
      const res = await apiClient.get<UserProfile>('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setUser(res.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch user profile:', err);

      setUser(null);
      setToken(null);
      localStorage.removeItem('auth_token');
      setError(err?.response?.data?.detail || err?.message || 'Authentication session expired.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUserProfile(token);
    } else {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
      setIsLoading(false);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (newToken: string) => {
    localStorage.setItem('auth_token', newToken);
    setToken(newToken);
    await fetchUserProfile(newToken);
  };

  const loginWithCredentials = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await authApi.login(email, password);
      localStorage.setItem('auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Login failed.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const registerWithCredentials = async (email: string, password: string, name: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await authApi.register(email, password, name);
      localStorage.setItem('auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Registration failed.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsDemoAttorney = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await authApi.demoLogin();
      localStorage.setItem('auth_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err: any) {
      console.warn('Demo login endpoint unreachable, falling back to local demo token:', err);
      const demoToken = 'test_token_:demo_attorney_01:attorney@legalai.example.com:Sarah Jenkins, Esq.';
      await login(demoToken);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
    setError(null);
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        login,
        loginWithCredentials,
        registerWithCredentials,
        loginAsDemoAttorney,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
