import React, { useState } from 'react';
import {
  FileText,
  Scissors,
  Binary,
  Layers,
  Sparkles,
  BookmarkCheck,
  ShieldCheck,
  AlertTriangle,
  ChevronRight,
  Info,
  CheckCircle2,
} from 'lucide-react';

interface PipelineStage {
  id: number;
  title: string;
  type: 'Deterministic' | 'Generative AI' | 'Hybrid / Algorithmic';
  icon: React.ElementType;
  description: string;
  technicalDetails: string;
  color: string;
}

const stages: PipelineStage[] = [
  {
    id: 1,
    title: 'Document Ingestion & Safe Parsing',
    type: 'Deterministic',
    icon: FileText,
    description: 'Validates file integrity, hashes content (SHA-256), and extracts clean text page-by-page using PyMuPDF.',
    technicalDetails: 'No LLM involved. Guarantees deterministic text extraction without hallucinations or omissions.',
    color: 'border-blue-300 bg-blue-50/50 text-blue-700',
  },
  {
    id: 2,
    title: 'Legal-Aware Semantic Chunking',
    type: 'Deterministic',
    icon: Scissors,
    description: 'Segments legal text into clause-aware chunks (400-800 tokens) with 15% overlap, preserving clause numbers.',
    technicalDetails: 'Respects legal syntax (e.g. "Section 4.1", "Article 2") so contractual provisions are never severed.',
    color: 'border-indigo-300 bg-indigo-50/50 text-indigo-700',
  },
  {
    id: 3,
    title: 'Dense & Sparse Embeddings',
    type: 'Generative AI',
    icon: Binary,
    description: 'Generates high-dimensional semantic embeddings (Gemini 768-d) and BM25 token frequencies for each chunk.',
    technicalDetails: 'Dense vectors capture legal semantics; sparse BM25 indices capture exact statutory citations and names.',
    color: 'border-purple-300 bg-purple-50/50 text-purple-700',
  },
  {
    id: 4,
    title: 'Hybrid Retrieval & RRF Ranking',
    type: 'Hybrid / Algorithmic',
    icon: Layers,
    description: 'Combines vector cosine similarity with BM25 keyword matching via Reciprocal Rank Fusion (k=60).',
    technicalDetails: 'Retrieves top-k candidate chunks with high recall across both conceptual and term-exact queries.',
    color: 'border-cyan-300 bg-cyan-50/50 text-cyan-700',
  },
  {
    id: 5,
    title: 'Context Window Assembly',
    type: 'Deterministic',
    icon: FileText,
    description: 'Filters, deduplicates, and formats retrieved evidence chunks with exact page and section metadata.',
    technicalDetails: 'Enforces token budgets and formats evidence as numbered reference blocks [1], [2] for the model.',
    color: 'border-emerald-300 bg-emerald-50/50 text-emerald-700',
  },
  {
    id: 6,
    title: 'Generative Synthesis (Gemini)',
    type: 'Generative AI',
    icon: Sparkles,
    description: 'Gemini 2.5 Flash synthesizes a tailored, plain-English legal analysis strictly based on injected context.',
    technicalDetails: 'Uses temperature=0.1, strict grounding prompts, and explicitly refuses queries unsupported by text.',
    color: 'border-amber-300 bg-amber-50/50 text-amber-700',
  },
  {
    id: 7,
    title: 'Evidentiary Citation Mapping',
    type: 'Deterministic',
    icon: BookmarkCheck,
    description: 'Parses bracketed citations [n] in generated text and links them back to exact document chunks and pages.',
    technicalDetails: 'Validates that every citation refers to an actual injected chunk, highlighting exact quoted phrases.',
    color: 'border-teal-300 bg-teal-50/50 text-teal-700',
  },
  {
    id: 8,
    title: 'Automated Grounding Verification',
    type: 'Hybrid / Algorithmic',
    icon: ShieldCheck,
    description: 'Extracts substantive claims and computes semantic NLI/token overlap against cited chunks to reject hallucinations.',
    technicalDetails: 'If a claim cannot be verified against the source text, status transitions to "insufficient_support".',
    color: 'border-emerald-400 bg-emerald-50/60 text-emerald-800',
  },
  {
    id: 9,
    title: 'Statutory Disclaimer Guardrails',
    type: 'Deterministic',
    icon: AlertTriangle,
    description: 'Attaches mandatory legal notices informing users that output is for informational purposes, not legal advice.',
    technicalDetails: 'Programmatically enforced at API level. Cannot be bypassed or stripped by user prompts.',
    color: 'border-rose-300 bg-rose-50/50 text-rose-700',
  },
];

export const AiPipelineVisualization: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<PipelineStage>(stages[5]); // Default to Generative Synthesis

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-600" aria-hidden="true" />
            <h2 className="text-lg font-bold text-slate-900">How Legal AI Works: 9-Stage Architecture</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Transparently separates Generative AI synthesis from deterministic verification and guardrails.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2 text-[11px] font-medium">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-600" aria-hidden="true" /> GenAI (Gemini)
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600" aria-hidden="true" /> Deterministic / Rules
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-600" aria-hidden="true" /> Hybrid Search
          </span>
        </div>
      </div>

      {/* Interactive Pipeline Steps */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-9 gap-2">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isSelected = selectedStage.id === stage.id;
          return (
            <button
              key={stage.id}
              onClick={() => setSelectedStage(stage)}
              aria-pressed={isSelected}
              aria-label={`Pipeline Stage 0${stage.id}: ${stage.title} (${stage.type})`}
              className={`p-3 rounded-lg border text-left transition relative flex flex-col justify-between h-28 group ${
                isSelected
                  ? 'border-indigo-600 ring-2 ring-indigo-100 bg-indigo-50/40 shadow-xs'
                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50 bg-white'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[10px] font-mono font-bold text-slate-600">
                  0{stage.id}
                </span>
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                    stage.type === 'Generative AI'
                      ? 'bg-purple-100 text-purple-700'
                      : stage.type === 'Deterministic'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-cyan-100 text-cyan-700'
                  }`}
                >
                  {stage.type === 'Generative AI' ? 'GenAI' : stage.type === 'Deterministic' ? 'Rules' : 'Hybrid'}
                </span>
              </div>

              <div className="mt-2">
                <Icon
                  className={`w-4 h-4 mb-1 ${
                    isSelected ? 'text-indigo-600' : 'text-slate-600 group-hover:text-slate-900'
                  }`}
                  aria-hidden="true"
                />
                <div className="text-[11px] font-bold text-slate-800 leading-tight line-clamp-2">
                  {stage.title}
                </div>
              </div>

              {idx < stages.length - 1 && (
                <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 pointer-events-none">
                  <ChevronRight className="w-3.5 h-3.5 text-slate-300" aria-hidden="true" />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Stage Detail Card */}
      <div className="p-4 rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/50 via-white to-purple-50/30">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-indigo-600 text-white shadow-xs shrink-0">
            {React.createElement(selectedStage.icon, { className: 'w-6 h-6', 'aria-hidden': 'true' })}
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-indigo-600 uppercase">
                Stage 0{selectedStage.id}
              </span>
              <span className="text-slate-300" aria-hidden="true">•</span>
              <h3 className="text-sm font-bold text-slate-900">{selectedStage.title}</h3>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  selectedStage.type === 'Generative AI'
                    ? 'bg-purple-100 text-purple-700 border border-purple-200'
                    : selectedStage.type === 'Deterministic'
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-cyan-100 text-cyan-700 border border-cyan-200'
                }`}
              >
                {selectedStage.type}
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {selectedStage.description}
            </p>
            <div className="pt-2 flex items-center gap-1.5 text-[11px] text-slate-600 font-medium">
              <Info className="w-3.5 h-3.5 text-indigo-500 shrink-0" aria-hidden="true" />
              <span>{selectedStage.technicalDetails}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
