import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../contexts/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { LegalDisclaimerBanner } from '../components/common/LegalDisclaimerBanner';
import { Navbar } from '../components/layout/Navbar';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { DocumentLibraryPage } from '../pages/DocumentLibraryPage';
import { ChatPage } from '../pages/ChatPage';
import { SettingsPage } from '../pages/SettingsPage';
import { checkHealth } from '../services/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const SimplePageLayout: React.FC<{ title: string; description: string }> = ({ title, description }) => (
  <div className="max-w-4xl mx-auto py-12 px-4 text-center">
    <h1 className="text-3xl font-bold text-slate-900 mb-4">{title}</h1>
    <p className="text-slate-600 mb-8">{description}</p>
    <Link to="/dashboard" className="text-sm font-semibold text-slate-900 underline hover:text-slate-700">
      &larr; Back to Dashboard
    </Link>
  </div>
);

export const App: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<'healthy' | 'error' | 'loading'>('loading');

  useEffect(() => {
    checkHealth()
      .then((res) => {
        if (res.status === 'healthy') {
          setBackendStatus('healthy');
        } else {
          setBackendStatus('error');
        }
      })
      .catch(() => {
        setBackendStatus('error');
      });
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-slate-50 font-sans">
            <LegalDisclaimerBanner />
            <Navbar backendStatus={backendStatus} />
            <main className="flex-1">
              <Routes>
                {/* Public routes */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Protected routes */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <DashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/documents"
                  element={
                    <ProtectedRoute>
                      <DocumentLibraryPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/chat"
                  element={
                    <ProtectedRoute>
                      <ChatPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <ProtectedRoute>
                      <SettingsPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};
