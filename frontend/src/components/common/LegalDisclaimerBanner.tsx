import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const LegalDisclaimerBanner: React.FC = () => {
  return (
    <aside aria-label="Legal Disclaimer" className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-amber-900 text-xs md:text-sm">
      <div className="max-w-7xl mx-auto flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" aria-hidden="true" />
        <p className="leading-snug">
          <strong className="font-semibold text-amber-950">Legal Disclaimer:</strong> This platform provides general legal information and document analysis for educational purposes. It does not provide legal advice, establish an attorney-client relationship, or replace consultation with a qualified legal professional.
        </p>
      </div>
    </aside>
  );
};
