import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  FileCheck2,
  CalendarCheck,
  Inbox,
  CheckCircle2,
  Clock,
  AlertTriangle,
  AlertOctagon,
  RefreshCw,
  BellRing,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { dashboardAPI, requestsAPI } from '../services/api';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';

export const DashboardPage = () => {
  const [summary, setSummary] = useState(null);
  const [overdue, setOverdue] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [triggerMessage, setTriggerMessage] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumRes, overRes, reqRes] = await Promise.all([
        dashboardAPI.getSummary(),
        dashboardAPI.getOverdue(),
        requestsAPI.list({ limit: 10 }),
      ]);
      setSummary(sumRes.data);
      setOverdue(overRes.data);
      setRequests(reqRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTriggerReminders = async () => {
    try {
      setTriggering(true);
      const res = await dashboardAPI.triggerReminders();
      const actions = res.data?.results?.actions || [];
      setTriggerMessage(
        actions.length > 0
          ? `Engine executed: ${actions.join('; ')}`
          : 'Scheduler check completed. All requests are up-to-date with no pending reminders.'
      );
      await loadData();
    } catch (err) {
      setTriggerMessage('Error executing reminder check.');
    } finally {
      setTriggering(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-500 flex items-center space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
          <span>Loading LOD2 Control Testing Dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Control Testing Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Second Line of Defense (LOD2) Autonomous Evidence Collection & Gemini AI Verification
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleTriggerReminders}
            disabled={triggering}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 shadow-sm transition-all disabled:opacity-50"
          >
            <BellRing className={`w-3.5 h-3.5 ${triggering ? 'animate-bounce' : ''}`} />
            <span>{triggering ? 'Running APScheduler...' : 'Trigger Reminders & Escalations'}</span>
          </button>
        </div>
      </div>

      {triggerMessage && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs flex items-center justify-between">
          <span>{triggerMessage}</span>
          <button onClick={() => setTriggerMessage(null)} className="font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Top 8 Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Controls"
          value={summary?.total_controls || 0}
          subtitle="Configured reusable controls"
          icon={ShieldCheck}
          color="blue"
        />
        <StatCard
          title="Active Assignments"
          value={summary?.active_assignments || 0}
          subtitle="Scope-control mappings"
          icon={FileCheck2}
          color="purple"
        />
        <StatCard
          title="Active Reviews"
          value={summary?.active_reviews || 0}
          subtitle="In-progress testing cycles"
          icon={CalendarCheck}
          color="slate"
        />
        <StatCard
          title="Total Requests"
          value={summary?.total_requests || 0}
          subtitle="All evidence submissions"
          icon={Inbox}
          color="blue"
        />
        <StatCard
          title="Complete"
          value={summary?.complete_requests || 0}
          subtitle="AI verified & accepted"
          icon={CheckCircle2}
          color="emerald"
        />
        <StatCard
          title="Pending"
          value={summary?.pending_requests || 0}
          subtitle="Awaiting user submission"
          icon={Clock}
          color="blue"
        />
        <StatCard
          title="Incomplete"
          value={summary?.incomplete_requests || 0}
          subtitle="Missing critical items"
          icon={AlertTriangle}
          color="amber"
        />
        <StatCard
          title="Overdue"
          value={summary?.overdue_requests || 0}
          subtitle="Past due deadline"
          icon={AlertOctagon}
          color="rose"
        />
      </div>

      {/* Overdue Alert Section if any */}
      {overdue.length > 0 && (
        <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center space-x-2 text-rose-800 font-bold text-sm mb-3">
            <AlertOctagon className="w-4 h-4 text-rose-600" />
            <span>Attention: {overdue.length} Overdue Evidence Request{overdue.length > 1 ? 's' : ''} Requiring Action</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {overdue.map((item) => (
              <div key={item.id} className="bg-white p-3.5 rounded-lg border border-rose-200 text-xs shadow-xs">
                <div className="flex justify-between items-start">
                  <span className="font-bold text-slate-800">{item.request_code}</span>
                  <span className="bg-rose-100 text-rose-800 font-bold px-2 py-0.5 rounded text-[10px]">
                    {item.days_overdue} days overdue
                  </span>
                </div>
                <p className="text-slate-600 font-medium mt-1 truncate">{item.control_name}</p>
                <div className="text-[11px] text-slate-500 mt-2">
                  Recipient: <span className="font-mono">{item.recipient}</span>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-100 flex justify-end">
                  <Link
                    to={`/evidence-requests/${item.id}`}
                    className="text-blue-600 hover:text-blue-800 font-semibold flex items-center space-x-1"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scope Distribution Bar */}
      {summary?.scope_distribution && Object.keys(summary.scope_distribution).length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-3">Requests by Scope Type</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.scope_distribution).map(([stype, count]) => (
              <div
                key={stype}
                className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs"
              >
                <span className="font-semibold text-slate-700">{stype}</span>
                <span className="bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded-full text-[11px]">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Requests Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Recent Evidence Requests</h3>
            <p className="text-xs text-slate-500">Live operational review requests and automated AI status</p>
          </div>
          <Link
            to="/evidence-requests"
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
          >
            <span>View All</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Request ID</th>
                <th className="px-5 py-3">Control</th>
                <th className="px-5 py-3">Scope & Recipient</th>
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
                    No requests found. Seed the database or create a new review.
                  </td>
                </tr>
              ) : (
                requests.map((req) => {
                  const scope = req.review?.assignment?.scope;
                  const control = req.review?.assignment?.control;
                  return (
                    <tr key={req.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-5 py-3.5 font-bold font-mono text-slate-900">
                        {req.request_code}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="font-semibold text-slate-800">{control?.control_code}</div>
                        <div className="text-slate-500 text-[11px] truncate max-w-xs">{control?.name}</div>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="font-medium text-slate-800">{scope?.name}</div>
                        <div className="text-slate-400 text-[11px] font-mono">{scope?.email}</div>
                      </td>
                      <td className="px-5 py-3.5 font-medium text-slate-600">
                        {new Date(req.due_date).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 font-medium">
                        {req.reminder_count} sent
                      </td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={req.status} />
                      </td>
                      <td className="px-5 py-3.5 text-right space-x-2">
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
    </div>
  );
};
