import React from 'react';

const statusStyles = {
  // Evidence request / Review statuses
  COMPLETE: 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20',
  COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20',
  PENDING: 'bg-blue-50 text-blue-700 border-blue-200 ring-blue-600/20',
  OPEN: 'bg-sky-50 text-sky-700 border-sky-200 ring-sky-600/20',
  IN_PROGRESS: 'bg-indigo-50 text-indigo-700 border-indigo-200 ring-indigo-600/20',
  SUBMITTED: 'bg-purple-50 text-purple-700 border-purple-200 ring-purple-600/20',
  PROCESSING: 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-600/20 animate-pulse',
  INCOMPLETE: 'bg-amber-50 text-amber-800 border-amber-300 ring-amber-600/20',
  OVERDUE: 'bg-rose-50 text-rose-700 border-rose-200 ring-rose-600/20',
  CANCELLED: 'bg-slate-100 text-slate-600 border-slate-200 ring-slate-600/20',
  
  // AI Validation statuses
  IRRELEVANT: 'bg-red-50 text-red-700 border-red-200 ring-red-600/20',
  LOW_CONFIDENCE: 'bg-orange-50 text-orange-700 border-orange-200 ring-orange-600/20',
  
  // Relevance
  HIGH: 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20',
  MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-600/20',
  LOW: 'bg-rose-50 text-rose-700 border-rose-200 ring-rose-600/20',

  // Active / Inactive
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20',
  INACTIVE: 'bg-slate-100 text-slate-600 border-slate-200 ring-slate-600/20',
};

export const StatusBadge = ({ status, className = '' }) => {
  const norm = (status || '').toUpperCase();
  const style = statusStyles[norm] || 'bg-slate-100 text-slate-700 border-slate-200 ring-slate-600/20';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style} ${className}`}>
      {status || 'UNKNOWN'}
    </span>
  );
};
