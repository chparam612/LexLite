import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  MessageSquare, 
  Upload, 
  Clock, 
  ShieldCheck, 
  ArrowRight,
  UserCheck
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Welcome Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 mb-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold mb-3 border border-emerald-200">
              <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Authenticated Workspace</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Welcome back, {user?.display_name || user?.email}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Tenant ID: <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{user?.id}</code> • Firebase UID: <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{user?.firebase_uid}</code>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/documents"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm"
            >
              <Upload className="w-4 h-4 text-amber-400" />
              <span>Upload Document</span>
            </Link>
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-700 text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              <MessageSquare className="w-4 h-4 text-slate-500" />
              <span>Start Analysis</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
        <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-600">Total Documents</span>
            <FileText className="w-5 h-5 text-slate-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">1</span>
            <span className="text-xs text-slate-500">active legal contract</span>
          </div>
        </div>

        <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-600">Verified Citations</span>
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">100%</span>
            <span className="text-xs text-emerald-600 font-medium">zero ungrounded claims</span>
          </div>
        </div>

        <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-600">Active Chats</span>
            <Clock className="w-5 h-5 text-slate-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">1</span>
            <span className="text-xs text-slate-500">conversation session</span>
          </div>
        </div>
      </div>

      {/* Recent Activity Card */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Recent Documents</h2>
          <Link to="/documents" className="text-sm font-medium text-slate-900 hover:text-slate-700 inline-flex items-center gap-1">
            <span>View Library</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        <div className="p-6">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-slate-900 flex items-center justify-center text-amber-400">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Master Services Agreement (Demo)</h3>
                <p className="text-xs text-slate-500">Jurisdiction: State of New York • 3 Pages • Status: Processed</p>
              </div>
            </div>
            <Link
              to="/chat"
              className="text-xs font-semibold text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded hover:bg-slate-100 transition-colors"
            >
              Ask Questions
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
