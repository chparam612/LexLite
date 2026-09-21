import React from 'react';
import { 
  ShieldCheck, 
  FileSearch, 
  CheckCircle2, 
  Lock, 
  Scale, 
  ArrowRight, 
  AlertCircle 
} from 'lucide-react';
import { Link } from 'react-router-dom';

const HOW_IT_WORKS_STEPS = [
  {
    step: 1,
    title: 'Upload PDF',
    description: 'Secure multi-tenant document upload with SHA-256 deduplication and encrypted storage.'
  },
  {
    step: 2,
    title: 'Legal Parsing',
    description: 'Detects Articles, Sections, Clauses, Definitions, Exceptions, and Provisos with page-awareness.'
  },
  {
    step: 3,
    title: 'Hybrid Retrieval',
    description: 'Combines pgvector dense semantic retrieval and keyword matching via Reciprocal Rank Fusion.'
  },
  {
    step: 4,
    title: 'Claim Verification',
    description: 'Every statement is cross-checked against source text chunks to eliminate hallucinations.'
  }
];

const CORE_FEATURES = [
  {
    icon: Scale,
    iconColor: 'text-amber-600',
    title: 'Rights & Obligations',
    description: 'Clearly isolate affirmative covenants, negative obligations, and permitted actions across parties.'
  },
  {
    icon: FileSearch,
    iconColor: 'text-blue-600',
    title: 'Deadlines & Penalties',
    description: 'Locate termination notice periods, cure windows, late fees, and liquidated damage clauses.'
  },
  {
    icon: AlertCircle,
    iconColor: 'text-rose-600',
    title: 'Conditions & Exceptions',
    description: 'Never miss critical qualifiers ("provided that", "unless otherwise agreed", "subject to Section 4").'
  }
];

const SECURITY_POINTS = [
  'Firebase Token Authentication',
  'IDOR Defense across all endpoints',
  'Zero Stack Trace or Secret Leakage',
  'Deterministic SHA-256 Storage Keys'
];

export const LandingPage: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-white to-slate-50 border-b border-slate-200 py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold mb-6 border border-slate-200">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Grounded Legal RAG with Claim-Level Citations</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-950 tracking-tight leading-tight">
              Legal Understanding, <br />
              <span className="text-slate-700">Backed by Exact Evidence</span>
            </h1>
            <p className="mt-6 text-lg text-slate-600 leading-relaxed">
              Upload legal agreements, policies, and contracts. Query clauses in natural language and receive grounded answers with verifiable page-level and clause-level citations.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 transition-all shadow-md"
              >
                <span>Analyze Your First Document</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-lg bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-all shadow-sm"
              >
                Sign In to Workspace
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-16 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">How It Works</h2>
            <p className="mt-2 text-slate-600">From raw PDF to verified legal intelligence in seconds.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {HOW_IT_WORKS_STEPS.map((item) => (
              <div key={item.step} className="p-6 rounded-xl bg-slate-50 border border-slate-200 flex flex-col">
                <div className="w-10 h-10 rounded-lg bg-slate-900 text-amber-400 flex items-center justify-center font-bold mb-4">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-16 bg-slate-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Intelligent Legal Analysis</h2>
            <p className="mt-2 text-slate-600">Understand the nuances that matter most in legal documents.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {CORE_FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <div key={feat.title} className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm">
                  <Icon className={`w-8 h-8 ${feat.iconColor} mb-4`} />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">{feat.title}</h3>
                  <p className="text-sm text-slate-600">{feat.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Security & Privacy */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-slate-900 rounded-2xl text-white p-8 md:p-12">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 text-amber-400 text-xs font-semibold mb-4 border border-slate-700">
                <Lock className="w-3.5 h-3.5" />
                <span>Enterprise Security & Data Isolation</span>
              </div>
              <h2 className="text-2xl md:text-3xl font-bold mb-4">Your Legal Data Remains Yours</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                All uploaded documents are isolated per user tenant with cryptographically enforced access policies. Document texts are never used to train public models, and prompt injection defense prevents document content from compromising system instructions.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-slate-300">
                {SECURITY_POINTS.map((point) => (
                  <div key={point} className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{point}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>


      {/* Footer */}
      <footer className="mt-auto bg-slate-100 border-t border-slate-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500 space-y-2">
          <p>© 2026 LEGAL AI — Assistance & Access Platform. All rights reserved.</p>
          <p className="max-w-2xl mx-auto">
            This platform provides general legal information and document analysis for educational purposes. It does not provide legal advice, establish an attorney-client relationship, or replace consultation with a qualified legal professional.
          </p>
        </div>
      </footer>
    </div>
  );
};
