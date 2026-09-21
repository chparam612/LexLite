import React from 'react';
import { Scale, Activity, LogOut, User as UserIcon, Sparkles } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface NavbarProps {
  backendStatus?: 'healthy' | 'error' | 'loading';
}

export const Navbar: React.FC<NavbarProps> = ({ backendStatus = 'healthy' }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-sm group-hover:bg-slate-800 transition-colors">
            <Scale className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <span className="font-bold text-lg text-slate-900 tracking-tight block">
              LEGAL AI
            </span>
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block -mt-1">
              Assistance & Access
            </span>
          </div>
        </Link>

        {isAuthenticated && (
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <Link to="/dashboard" className="hover:text-slate-900 transition-colors">
              Dashboard
            </Link>
            <Link to="/documents" className="hover:text-slate-900 transition-colors">
              Documents
            </Link>
            <Link to="/chat" className="hover:text-slate-900 transition-colors">
              Chat
            </Link>
            <Link
              to="/demo"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-semibold transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Demo Hub
            </Link>
            <Link to="/evaluation" className="hover:text-slate-900 transition-colors">
              Evaluation
            </Link>
            <Link to="/settings" className="hover:text-slate-900 transition-colors">
              Settings
            </Link>
          </nav>
        )}

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
            <Activity className="w-3.5 h-3.5 text-emerald-500" />
            <span>API {backendStatus === 'healthy' ? 'Online' : 'Checking'}</span>
          </div>

          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-800">
                <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                <span className="max-w-[140px] truncate">{user?.display_name || user?.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/evaluation"
                className="text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-lg transition-colors"
              >
                Evaluation Suite
              </Link>
              <Link
                to="/login"
                className="text-sm font-medium text-slate-700 hover:text-slate-900 px-3 py-2 rounded-md hover:bg-slate-50 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 px-4 py-2 rounded-lg shadow-sm transition-all"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
