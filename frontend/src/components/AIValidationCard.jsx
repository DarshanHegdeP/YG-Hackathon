import React from 'react';
import { Sparkles, CheckCircle2, AlertCircle, HelpCircle, ShieldCheck } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export const AIValidationCard = ({ validation }) => {
  if (!validation) {
    return (
      <div className="bg-slate-50 border border-dashed border-slate-300 rounded-xl p-8 text-center text-slate-400">
        <Sparkles className="w-8 h-8 mx-auto mb-2 text-slate-400 opacity-60" />
        <p className="text-sm font-medium">No AI Validation performed yet.</p>
        <p className="text-xs text-slate-400 mt-1">Upload evidence to run automated Gemini verification.</p>
      </div>
    );
  }

  const confidencePct = Math.round((validation.confidence || 0) * 100);

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-linear-to-r from-blue-900 via-indigo-900 to-slate-900 p-5 text-white flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-blue-500/20 border border-blue-400/30 text-blue-300">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold tracking-wide uppercase">Gemini AI Audit Assessment</h4>
            <p className="text-xs text-blue-200/80">Automated LOD2 Evidence Evaluation Engine</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="text-xs text-blue-200">Confidence</div>
            <div className="text-lg font-bold text-white">{confidencePct}%</div>
          </div>
          <StatusBadge status={validation.status} className="text-xs px-3 py-1 uppercase" />
        </div>
      </div>

      <div className="p-6 space-y-5">
        {/* Confidence Progress Bar */}
        <div>
          <div className="flex justify-between text-xs text-slate-500 font-medium mb-1">
            <span>Model Confidence Score</span>
            <span>{confidencePct}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                confidencePct >= 80 ? 'bg-emerald-500' : confidencePct >= 60 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>

        {/* Reason summary box */}
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Audit Assessment Summary
          </span>
          <p className="text-sm text-slate-800 leading-relaxed font-medium">
            "{validation.reason}"
          </p>
        </div>

        {/* Findings and Missing Information side by side or stacked */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Findings */}
          <div className="p-4 rounded-lg bg-emerald-50/60 border border-emerald-100">
            <h5 className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Verified Audit Findings</span>
            </h5>
            {validation.findings && validation.findings.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-emerald-900">
                {validation.findings.map((finding, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{finding}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-400 italic">No positive findings noted.</p>
            )}
          </div>

          {/* Missing Information */}
          <div className="p-4 rounded-lg bg-rose-50/60 border border-rose-100">
            <h5 className="text-xs font-bold text-rose-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <AlertCircle className="w-4 h-4 text-rose-600" />
              <span>Missing Required Evidence</span>
            </h5>
            {validation.missing_information && validation.missing_information.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-rose-900">
                {validation.missing_information.map((item, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-rose-500 font-bold">•</span>
                    <span className="font-semibold">{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-emerald-700 font-medium">✓ None. All mandatory requirements satisfied!</p>
            )}
          </div>
        </div>

        {/* Footer meta */}
        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>Evaluated by: <strong className="text-slate-600">{validation.model}</strong></span>
          <span>Relevance: <strong className="text-slate-600">{validation.relevance}</strong></span>
          <span>Timestamp: {new Date(validation.created_at).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};
