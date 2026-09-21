import React from 'react';
import {
  X,
  FileText,
  Download,
  MessageSquare,
  ShieldCheck,
  Calendar,
  Layers,
  Scale,
  Hash,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { DocumentItem, getDocumentDownloadUrl } from '../../services/documentApi';

interface DocumentPreviewModalProps {
  document: DocumentItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  document,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-xl w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-900 text-amber-400 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 line-clamp-1">{document.title}</h2>
              <span className="text-xs text-slate-500">Legal Document Overview & Preview</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 block font-medium flex items-center gap-1">
                <Scale className="w-3.5 h-3.5 text-slate-500" /> Jurisdiction
              </span>
              <span className="font-semibold text-slate-800 mt-1 block">
                {document.jurisdiction || 'General Commercial / Unspecified'}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 block font-medium flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-slate-500" /> Scope & Size
              </span>
              <span className="font-semibold text-slate-800 mt-1 block">
                {document.page_count} Pages • {(document.file_size / 1024).toFixed(1)} KB
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 block font-medium flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-500" /> Ingested Date
              </span>
              <span className="font-semibold text-slate-800 mt-1 block">
                {new Date(document.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 block font-medium flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> Processing Status
              </span>
              <span className="font-semibold text-emerald-700 mt-1 block capitalize">
                {document.status === 'completed' ? 'Verified & Indexed' : document.status}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-[11px] font-mono text-slate-600">
            <div className="flex items-center gap-1 font-semibold text-slate-500 uppercase text-[10px] mb-1">
              <Hash className="w-3 h-3" /> SHA-256 Checksum Integrity
            </div>
            <div className="truncate text-slate-700 bg-white p-2 rounded border border-slate-200 select-all">
              {document.checksum}
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <a
            href={getDocumentDownloadUrl(document.id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 hover:bg-white text-slate-700 text-xs font-semibold transition"
          >
            <Download className="w-3.5 h-3.5" />
            Download Original PDF
          </a>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-2 rounded-lg text-slate-600 hover:text-slate-900 text-xs font-semibold transition"
            >
              Close
            </button>
            <Link
              to={`/chat?doc=${document.id}`}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition shadow-xs"
            >
              <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
              Ask AI Questions
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
