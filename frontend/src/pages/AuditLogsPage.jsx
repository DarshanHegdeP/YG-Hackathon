import React, { useState, useEffect } from 'react';
import { History, Search, Shield, Filter } from 'lucide-react';
import { auditAPI } from '../services/api';

export const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  const loadLogs = async () => {
    try {
      setLoading(true);
      const res = await auditAPI.getLogs({
        entity_type: entityFilter || undefined,
        action: actionFilter || undefined,
        limit: 100
      });
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [entityFilter, actionFilter]);

  const getActionColor = (action) => {
    if (action.includes('CREATED')) return 'text-blue-700 bg-blue-50 border-blue-200';
    if (action.includes('SENT') || action.includes('REMINDER')) return 'text-amber-800 bg-amber-50 border-amber-200';
    if (action.includes('ESCALATION')) return 'text-rose-800 bg-rose-50 border-rose-200';
    if (action.includes('COMPLETE')) return 'text-emerald-800 bg-emerald-50 border-emerald-200';
    return 'text-slate-700 bg-slate-100 border-slate-200';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Compliance Audit Trail</h1>
          <p className="text-sm text-slate-500 mt-1">
            Immutable system audit logs tracking all control changes, AI decisions, and communications
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <select
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="bg-white px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 shadow-xs"
        >
          <option value="">All Entity Types</option>
          <option value="control">Control</option>
          <option value="scope">Scope</option>
          <option value="control_assignment">Assignment</option>
          <option value="review">Review</option>
          <option value="evidence_request">Evidence Request</option>
          <option value="evidence">Evidence</option>
          <option value="ai_validation">AI Validation</option>
          <option value="user">User</option>
        </select>

        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="bg-white px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 shadow-xs"
        >
          <option value="">All Action Types</option>
          <option value="CONTROL_CREATED">CONTROL_CREATED</option>
          <option value="REVIEW_CREATED">REVIEW_CREATED</option>
          <option value="EVIDENCE_REQUEST_CREATED">EVIDENCE_REQUEST_CREATED</option>
          <option value="EVIDENCE_UPLOADED">EVIDENCE_UPLOADED</option>
          <option value="EVIDENCE_PROCESSED_AND_VALIDATED">EVIDENCE_PROCESSED_AND_VALIDATED</option>
          <option value="MANUAL_REMINDER_SENT">MANUAL_REMINDER_SENT</option>
          <option value="MANUAL_ESCALATION_SENT">MANUAL_ESCALATION_SENT</option>
          <option value="REQUEST_MARKED_COMPLETE">REQUEST_MARKED_COMPLETE</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-5 py-3">Timestamp</th>
              <th className="px-5 py-3">Actor</th>
              <th className="px-5 py-3">Action</th>
              <th className="px-5 py-3">Target Entity</th>
              <th className="px-5 py-3">Audit Metadata</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {logs.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-5 py-8 text-center text-slate-400">
                  {loading ? 'Loading audit records...' : 'No audit records matching criteria.'}
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-slate-500 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 font-semibold text-slate-800">
                    {log.user_name || 'System / Engine'}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getActionColor(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    <span className="font-semibold text-slate-800">{log.entity_type}</span>
                    {log.entity_id && <span className="text-slate-400 font-mono text-[10px] ml-1">#{log.entity_id}</span>}
                  </td>
                  <td className="px-5 py-3.5 text-slate-500 font-mono text-[11px] max-w-xs truncate">
                    {log.metadata_json && Object.keys(log.metadata_json).length > 0
                      ? JSON.stringify(log.metadata_json)
                      : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
