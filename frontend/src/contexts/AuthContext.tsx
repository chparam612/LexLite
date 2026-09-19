import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, AuthContextType } from '../types/auth';
import { apiClient } from '../services/api';

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
      setError(err?.response?.data?.detail || 'Authentication failed');
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

  const login = async (newToken: string) => {
    localStorage.setItem('auth_token', newToken);
    setToken(newToken);
    await fetchUserProfile(newToken);
  };

  const loginAsDemoAttorney = async () => {
    const demoToken = 'test_token_:demo_attorney_01:attorney@legalai.example.com:Sarah Jenkins, Esq.';
    await login(demoToken);
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
