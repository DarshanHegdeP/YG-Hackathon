import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Inbox, ExternalLink, ChevronRight, Bell, AlertTriangle } from 'lucide-react';
import { requestsAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export const EvidenceRequestsPage = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  const loadRequests = async () => {
    try {
      setLoading(true);
      const res = await requestsAPI.list({
        status: statusFilter || undefined,
        search: search || undefined
      });
      setRequests(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, [statusFilter, search]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Evidence Requests Registry</h1>
          <p className="text-sm text-slate-500 mt-1">
            Tracking submission statuses, AI verification outcomes, and automated reminder states
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 flex items-center bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
          <Search className="w-4 h-4 text-slate-400 ml-1" />
          <input
            type="text"
            placeholder="Search by request code (e.g. REQ-2026-0001)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-transparent border-none text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden pl-3"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 shadow-xs"
        >
          <option value="">All Statuses</option>
          <option value="PENDING">PENDING</option>
          <option value="SUBMITTED">SUBMITTED</option>
          <option value="PROCESSING">PROCESSING</option>
          <option value="INCOMPLETE">INCOMPLETE</option>
          <option value="COMPLETE">COMPLETE</option>
          <option value="OVERDUE">OVERDUE</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-5 py-3">Request Code</th>
              <th className="px-5 py-3">Control & Name</th>
              <th className="px-5 py-3">Target Scope</th>
              <th className="px-5 py-3">Due Date</th>
              <th className="px-5 py-3">Reminders</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {requests.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-5 py-8 text-center text-slate-400">
                  {loading ? 'Loading requests...' : 'No evidence requests found.'}
                </td>
              </tr>
            ) : (
              requests.map((req) => {
                const ctrl = req.review?.assignment?.control;
                const scope = req.review?.assignment?.scope;
                return (
                  <tr key={req.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-3.5 font-bold font-mono text-slate-900">
                      {req.request_code}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-800">{ctrl?.control_code}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-xs">{ctrl?.name}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-slate-900">{scope?.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{scope?.email}</div>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-700">
                      {new Date(req.due_date).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-slate-600 font-medium">
                      {req.reminder_count} sent
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={req.status} />
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      <a
                        href={`/submit/${req.secure_token}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center space-x-1 text-slate-500 hover:text-slate-800 text-[11px] font-semibold"
                        title="Open Public Submitter Page"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Submit Link</span>
                      </a>
                      <Link
                        to={`/evidence-requests/${req.id}`}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
