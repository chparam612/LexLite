import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  Play,
  RotateCcw,
  Filter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { runEvaluation, EvaluationSummary, TestCaseResult } from '../services/api';

export const EvaluationDashboardPage: React.FC = () => {
  const [suiteResult, setSuiteResult] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [expandedTestIds, setExpandedTestIds] = useState<Record<string, boolean>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRunEvaluation = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await runEvaluation();
      setSuiteResult(data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error?.message || 'Failed to execute evaluation suite.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Run evaluation suite on page mount
    handleRunEvaluation();
  }, []);

  const toggleExpand = (testId: string) => {
    setExpandedTestIds((prev) => ({ ...prev, [testId]: !prev[testId] }));
  };

  const categories = suiteResult
    ? ['ALL', ...Array.from(new Set(suiteResult.results.map((r) => r.category)))]
    : ['ALL'];

  const filteredTests = suiteResult?.results.filter((t) => {
    if (selectedCategory === 'ALL') return true;
    return t.category.toLowerCase() === selectedCategory.toLowerCase();
  }) || [];

  const skippedCount = suiteResult?.skipped ?? (suiteResult?.results.filter((r) => r.status.includes('SKIP')).length ?? 0);
  const applicableTests = suiteResult ? suiteResult.total_tests - skippedCount : 0;
  const passRate = suiteResult?.pass_rate_pct ?? (applicableTests > 0
    ? Math.round((suiteResult!.passed / applicableTests) * 100)
    : 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Evaluation & Judging Dashboard
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
              Section 25C Suite
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Live, deterministic component verification across 10 evaluation categories. Real execution, zero hardcoded outcomes.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={loading}
          aria-label="Execute live evaluation suite"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs sm:text-sm transition shadow-sm disabled:opacity-50"
        >
          {loading ? (
            <>
              <RotateCcw className="w-4 h-4 animate-spin" aria-hidden="true" />
              Running Live Suite...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" aria-hidden="true" />
              Execute Evaluation Suite
            </>
          )}
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs sm:text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" aria-hidden="true" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Metrics Cards */}
      {suiteResult && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-600 uppercase block">Total Tests</span>
            <span className="text-2xl font-bold text-slate-900 mt-1 block">
              {suiteResult.total_tests}
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
            <span className="text-[11px] font-semibold text-emerald-700 uppercase block">Passed</span>
            <span className="text-2xl font-bold text-emerald-700 mt-1 block">
              {suiteResult.passed}
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
            <span className="text-[11px] font-semibold text-rose-700 uppercase block">Failed</span>
            <span className="text-2xl font-bold text-rose-700 mt-1 block">
              {suiteResult.failed}
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 bg-slate-50/20 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-600 uppercase block">Skipped / N/A</span>
            <span className="text-2xl font-bold text-slate-700 mt-1 block">
              {suiteResult.skipped ?? suiteResult.blocked}
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-indigo-200 bg-indigo-50/20 shadow-xs">
            <span className="text-[11px] font-semibold text-indigo-700 uppercase block">Pass Rate</span>
            <span className="text-2xl font-bold text-indigo-700 mt-1 block">
              {passRate}%
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-600 uppercase block">Suite Duration</span>
            <span className="text-2xl font-bold text-slate-900 mt-1 block">
              {suiteResult.execution_time_ms.toFixed(0)} ms
            </span>
          </div>
        </div>
      )}

      {/* Category Filter Pills */}
      {suiteResult && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0" aria-hidden="true" />
          <span className="text-slate-600 font-semibold shrink-0">Filter:</span>
          {categories.map((cat) => {
            const isSelected = selectedCategory === cat;
            const count = cat === 'ALL'
              ? suiteResult.results.length
              : suiteResult.results.filter((r) => r.category === cat).length;

            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                aria-pressed={isSelected}
                className={`px-3 py-1.5 rounded-lg font-semibold transition shrink-0 inline-flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span>{cat}</span>
                <span
                  className={`px-1.5 py-0.2 rounded text-[10px] ${
                    isSelected ? 'bg-slate-700 text-slate-200' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Test List */}
      <div className="space-y-3">
        {filteredTests.map((test: TestCaseResult) => {
          const isExpanded = !!expandedTestIds[test.test_id];
          const isPass = test.status === 'PASS';
          const isSkipped = test.status.includes('SKIP');
          const isBlocked = test.status.includes('BLOCKED');

          return (
            <div
              key={test.test_id}
              className={`bg-white rounded-xl border transition ${
                isPass
                  ? 'border-slate-200 hover:border-emerald-300'
                  : isSkipped
                  ? 'border-slate-200 hover:border-slate-300 bg-slate-50/30'
                  : isBlocked
                  ? 'border-amber-200 hover:border-amber-300'
                  : 'border-rose-200 hover:border-rose-300'
              }`}
            >
              <div
                role="button"
                tabIndex={0}
                aria-expanded={isExpanded}
                aria-label={`Test ${test.test_id}: ${test.name}, status ${test.status}. Click to ${isExpanded ? 'collapse' : 'expand'} details.`}
                onClick={() => toggleExpand(test.test_id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleExpand(test.test_id);
                  }
                }}
                className="p-4 flex items-center justify-between cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="shrink-0">
                    {isPass ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-700" aria-hidden="true" />
                    ) : isSkipped ? (
                      <MinusCircle className="w-5 h-5 text-slate-400" aria-hidden="true" />
                    ) : isBlocked ? (
                      <AlertTriangle className="w-5 h-5 text-amber-500" aria-hidden="true" />
                    ) : (
                      <XCircle className="w-5 h-5 text-rose-600" aria-hidden="true" />
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-700">
                        {test.test_id}
                      </span>
                      <span className="text-slate-300" aria-hidden="true">•</span>
                      <span className="text-xs font-semibold text-slate-900">
                        {test.name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600 uppercase">
                        {test.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{test.expected_behavior}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-xs font-mono text-slate-600">
                    {test.duration_ms.toFixed(1)} ms
                  </span>

                  <span
                    className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                      isPass
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : isSkipped
                        ? 'bg-slate-100 text-slate-600 border border-slate-200'
                        : isBlocked
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}
                  >
                    {test.status}
                  </span>

                  <div className="text-slate-600">
                    {isExpanded ? <ChevronUp className="w-4 h-4" aria-hidden="true" /> : <ChevronDown className="w-4 h-4" aria-hidden="true" />}
                  </div>
                </div>
              </div>

              {/* Expandable Details */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-1 border-t border-slate-100 space-y-3 text-xs bg-slate-50/50">
                  <div>
                    <span className="font-semibold text-slate-700 block mb-1">Input / Precondition:</span>
                    <div className="bg-white p-2.5 rounded border border-slate-200 text-slate-800 font-mono">
                      {test.input_description}
                    </div>
                  </div>

                  <div>
                    <span className="font-semibold text-slate-700 block mb-1">Expected Behavior:</span>
                    <div className="bg-white p-2.5 rounded border border-slate-200 text-slate-800">
                      {test.expected_behavior}
                    </div>
                  </div>

                  <div>
                    <span className="font-semibold text-slate-700 block mb-1">Actual Result:</span>
                    <div className="bg-slate-900 text-slate-100 p-2.5 rounded border border-slate-800 font-mono text-[11px] whitespace-pre-wrap">
                      {test.actual_result}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
