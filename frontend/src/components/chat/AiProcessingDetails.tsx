import React, { useState } from 'react';
import {
  Cpu,
  Clock,
  ShieldCheck,
  AlertCircle,
  Database,
  ChevronDown,
  ChevronUp,
  Layers,
  Sparkles,
  Zap,
} from 'lucide-react';
import { ProcessingDetails } from '../../services/api';

interface AiProcessingDetailsProps {
  details?: ProcessingDetails;
  modelName?: string;
}

export const AiProcessingDetails: React.FC<AiProcessingDetailsProps> = ({ details, modelName }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!details) return null;

  const isVerified = details.verification_status === 'verified' || details.verification_status === 'supported';
  const isInsufficient = details.verification_status === 'insufficient_support' || details.verification_status === 'insufficient_evidence';

  const totalLatency = details.latency_ms ?? details.total_latency_ms ?? 0;
  const candidateChunks = details.candidate_chunks ?? details.candidate_chunks_retrieved ?? 0;
  const contextChunks = details.context_chunks ?? details.context_chunks_used ?? 0;
  const retrievalLatency = details.retrieval_latency_ms;
  const generationLatency = details.generation_latency_ms;

  const formatRetrievalMethod = (method?: string) => {
    switch (method) {
      case 'hybrid_dense_sparse_rrf':
      case 'hybrid':
        return 'Hybrid Dense (Embeddings) + Sparse (BM25) with RRF';
      case 'vector_search':
        return 'Dense Vector Semantic Search';
      case 'bm25_text_search':
        return 'Sparse BM25 Keyword Search';
      default:
        return method || 'Grounded Document Retrieval';
    }
  };

  return (
    <div className="mt-2 text-xs border border-slate-200 rounded-lg overflow-hidden bg-slate-50/70 transition-all">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-1.5 flex items-center justify-between text-left hover:bg-slate-100/70 text-slate-600 transition"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span className="font-semibold text-slate-700">AI Grounding & Processing Trace</span>
          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${
              isVerified
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : isInsufficient
                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}
          >
            {isVerified ? (
              <>
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                Verified Grounded
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3 text-amber-600" />
                {details.verification_status || 'Trace Recorded'}
              </>
            )}
          </span>
          <span className="text-[10px] text-slate-400 font-mono">
            {typeof totalLatency === 'number' ? totalLatency.toFixed(0) : '0'}ms
          </span>
        </div>
        <div className="flex items-center text-slate-400">
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-3 border-t border-slate-200 bg-white space-y-2.5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="p-2 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] font-medium text-slate-500 uppercase flex items-center gap-1">
                <Database className="w-3 h-3 text-indigo-500" /> Candidate Chunks
              </div>
              <div className="text-sm font-bold text-slate-800 mt-0.5">
                {candidateChunks}
              </div>
            </div>

            <div className="p-2 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] font-medium text-slate-500 uppercase flex items-center gap-1">
                <Layers className="w-3 h-3 text-indigo-500" /> Context Injected
              </div>
              <div className="text-sm font-bold text-slate-800 mt-0.5">
                {contextChunks}
              </div>
            </div>

            <div className="p-2 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] font-medium text-slate-500 uppercase flex items-center gap-1">
                <Clock className="w-3 h-3 text-indigo-500" /> Retrieval
              </div>
              <div className="text-sm font-bold text-slate-800 mt-0.5">
                {typeof retrievalLatency === 'number'
                  ? `${retrievalLatency.toFixed(1)} ms`
                  : `${(typeof totalLatency === 'number' ? totalLatency : 0).toFixed(1)} ms`}
              </div>
            </div>

            <div className="p-2 rounded bg-slate-50 border border-slate-100">
              <div className="text-[10px] font-medium text-slate-500 uppercase flex items-center gap-1">
                <Cpu className="w-3 h-3 text-indigo-500" /> Synthesis
              </div>
              <div className="text-sm font-bold text-slate-800 mt-0.5">
                {typeof generationLatency === 'number'
                  ? `${generationLatency.toFixed(1)} ms`
                  : (details.reranking_used ? 'RRF Fused' : 'Synthesized')}
              </div>
            </div>
          </div>

          <div className="space-y-1 text-[11px] text-slate-600 bg-slate-50/70 p-2.5 rounded border border-slate-100">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700">Retrieval Pipeline:</span>
              <span className="font-mono text-[10px] bg-slate-200/80 px-1.5 py-0.5 rounded text-slate-800">
                {formatRetrievalMethod(details.retrieval_method)}
              </span>
            </div>
            {(modelName || details.model_name) && (
              <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                <span className="font-semibold text-slate-700">Generative Model:</span>
                <span className="font-mono text-[10px] text-indigo-600">
                  {modelName || details.model_name}
                </span>
              </div>
            )}
            <div className="flex items-center gap-1.5 pt-1 text-[10px] text-slate-500 border-t border-slate-100">
              <Zap className="w-3 h-3 text-amber-500 shrink-0" />
              <span>
                Real-time dynamic synthesis strictly anchored to retrieved document citations. No canned responses.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
