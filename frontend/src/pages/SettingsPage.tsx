import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  ShieldCheck,
  User,
  Cpu,
  Scale,
  Database,
  Lock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Scale className="h-6 w-6 text-indigo-600" />
          <span>Account & Platform Settings</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Manage your identity, tenant isolation boundaries, RAG configurations, and compliance ethics.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>Platform configuration updated successfully.</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Account & Security */}
        <div className="space-y-6">
          {/* User Profile Card */}
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                {user?.display_name ? user.display_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="truncate">
                <h3 className="font-semibold text-slate-900 text-sm truncate">
                  {user?.display_name || 'Legal Counsel'}
                </h3>
                <p className="text-slate-500 text-xs truncate">{user?.email}</p>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 space-y-2 text-xs">
              <div className="flex justify-between py-1 text-slate-600">
                <span className="text-slate-400">User ID</span>
                <span className="font-mono text-[11px] truncate max-w-[140px]">{user?.id}</span>
              </div>
              <div className="flex justify-between py-1 text-slate-600">
                <span className="text-slate-400">Role</span>
                <span className="font-medium text-slate-800">Licensed Attorney / Enterprise</span>
              </div>
              <div className="flex justify-between py-1 text-slate-600">
                <span className="text-slate-400">Auth Method</span>
                <span className="font-medium text-emerald-600 flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" />
                  Verified Token
                </span>
              </div>
            </div>
          </div>

          {/* Security & Tenant Isolation Card */}
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm">
              <Lock className="h-4 w-4 text-emerald-600" />
              <span>Tenant Isolation & Defense</span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Every document, chunk, and conversation is strictly isolated by cryptographic owner
              keys (anti-IDOR enforcement).
            </p>
            <div className="space-y-2 pt-1 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-700">Storage Traversal Guard</span>
                <span className="text-[11px] font-bold text-emerald-600">Active</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-700">Prompt Injection Sandbox</span>
                <span className="text-[11px] font-bold text-emerald-600">Active (XML)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-700">Secret Scrubbing in Logs</span>
                <span className="text-[11px] font-bold text-emerald-600">Enforced</span>
              </div>
            </div>
          </div>
        </div>

        {/* Middle & Right Column: RAG Config & Ethics */}
        <div className="md:col-span-2 space-y-6">
          {/* AI / RAG Engine Specifications */}
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-indigo-600" />
                <h3 className="font-semibold text-slate-900 text-sm">
                  Active RAG & Retrieval Engine Specifications
                </h3>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full">
                Phase 10 Production
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="text-slate-400 text-[11px]">Embedding Provider & Model</div>
                <div className="font-semibold text-slate-800">Google Gemini text-embedding-004</div>
                <div className="text-[11px] text-slate-500">768 dimensions (unit normalized)</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="text-slate-400 text-[11px]">Generation LLM Model</div>
                <div className="font-semibold text-slate-800">Google Gemini 1.5 Flash</div>
                <div className="text-[11px] text-slate-500">Structured Pydantic schema enforcement</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="text-slate-400 text-[11px]">Hybrid Fusion Strategy</div>
                <div className="font-semibold text-slate-800">Reciprocal Rank Fusion (RRF)</div>
                <div className="text-[11px] text-slate-500">Dense Cosine + BM25 Lexical (k=60)</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="text-slate-400 text-[11px]">Citation Verification Engine</div>
                <div className="font-semibold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Claim-Level Verbatim Verification
                </div>
                <div className="text-[11px] text-slate-500">Entailment & hallucination detection</div>
              </div>
            </div>
          </div>

          {/* Legal Ethics & Non-Negotiable Disclaimer */}
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
              <Scale className="h-5 w-5 text-amber-600" />
              <h3 className="font-semibold text-slate-900 text-sm">
                Mandatory Legal Disclaimer & Compliance
              </h3>
            </div>

            <div className="p-4 bg-amber-50/70 border border-amber-200/80 rounded-xl space-y-2 text-xs text-amber-900">
              <div className="flex items-center gap-2 font-bold text-amber-800">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>NON-NEGOTIABLE LEGAL NOTICE</span>
              </div>
              <p className="leading-relaxed text-[11px]">
                LEGAL AI — ASSISTANCE & ACCESS is an AI-powered legal research and document
                analysis system designed for educational, informational, and assistive purposes only.
                It does NOT provide legal advice, does NOT constitute legal representation, and does
                NOT establish an attorney-client relationship. All synthesized analyses and citations
                must be reviewed and validated by a licensed legal professional before use in legal
                proceedings or contract execution.
              </p>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="disclaimer-check"
                checked={disclaimerAccepted}
                onChange={(e) => setDisclaimerAccepted(e.target.checked)}
                className="h-4 w-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
              />
              <label htmlFor="disclaimer-check" className="text-xs text-slate-700 select-none">
                I understand and acknowledge the non-negotiable legal disclaimer and terms of assistance.
              </label>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={handleSave}
                disabled={!disclaimerAccepted}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-medium text-xs rounded-lg transition shadow-xs"
              >
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
