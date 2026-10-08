import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Calendar, Clock, ChevronRight, CheckCircle2 } from 'lucide-react';
import { reviewsAPI, assignmentsAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const ReviewsPage = () => {
  const [reviews, setReviews] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const { isReviewer } = useAuth();

  // Form state
  const [assignmentId, setAssignmentId] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [revRes, asRes] = await Promise.all([
        reviewsAPI.list({ status: statusFilter || undefined }),
        assignmentsAPI.list(),
      ]);
      setReviews(revRes.data);
      setAssignments(asRes.data);
      if (asRes.data.length > 0) setAssignmentId(asRes.data[0].id);

      // Default dates (e.g. current quarter)
      const now = new Date();
      const past = new Date(now);
      past.setDate(past.getDate() - 90);
      const due = new Date(now);
      due.setDate(due.getDate() + 7);

      setPeriodStart(past.toISOString().split('T')[0]);
      setPeriodEnd(now.toISOString().split('T')[0]);
      setDueDate(due.toISOString().split('T')[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleCreateReview = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await reviewsAPI.create({
        control_assignment_id: parseInt(assignmentId),
        period_start: new Date(periodStart).toISOString(),
        period_end: new Date(periodEnd).toISOString(),
        due_date: new Date(dueDate).toISOString(),
        status: 'OPEN',
        create_request: true
      });
      setShowModal(false);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initiate review.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Control Review Cycles</h1>
          <p className="text-sm text-slate-500 mt-1">
            Period-specific testing cycles and automated evidence request generation
          </p>
        </div>

        {isReviewer && (
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Initiate New Review</span>
          </button>
        )}
      </div>

      <div className="flex justify-end">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 shadow-xs"
        >
          <option value="">All Review Statuses</option>
          <option value="OPEN">OPEN</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="OVERDUE">OVERDUE</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-5 py-3">Control & Code</th>
              <th className="px-5 py-3">Scope Target</th>
              <th className="px-5 py-3">Testing Period</th>
              <th className="px-5 py-3">Submission Due Date</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {reviews.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-5 py-8 text-center text-slate-400">
                  {loading ? 'Loading reviews...' : 'No review cycles found.'}
                </td>
              </tr>
            ) : (
              reviews.map((rev) => (
                <tr key={rev.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5">
                    <span className="font-bold font-mono text-blue-600 mr-2">
                      {rev.assignment?.control?.control_code}
                    </span>
                    <span className="font-semibold text-slate-900">{rev.assignment?.control?.name}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="font-medium text-slate-800">{rev.assignment?.scope?.name}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{rev.assignment?.scope?.email}</div>
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    {new Date(rev.period_start).toLocaleDateString()} to {new Date(rev.period_end).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-3.5 font-medium text-slate-700">
                    {new Date(rev.due_date).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={rev.status} />
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <Link
                      to={`/reviews/${rev.id}`}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Initiate Review Cycle</h3>
            <p className="text-xs text-slate-500 mb-4">
              Select an active control assignment and create period review request.
            </p>

            {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-xs rounded-lg">{error}</div>}

            <form onSubmit={handleCreateReview} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Control Assignment</label>
                <select
                  value={assignmentId}
                  onChange={(e) => setAssignmentId(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  {assignments.map((as) => (
                    <option key={as.id} value={as.id}>
                      {as.control?.control_code} → {as.scope?.name} ({as.frequency})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Period Start</label>
                  <input
                    type="date"
                    required
                    value={periodStart}
                    onChange={(e) => setPeriodStart(e.target.value)}
                    className="w-full text-xs p-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Period End</label>
                  <input
                    type="date"
                    required
                    value={periodEnd}
                    onChange={(e) => setPeriodEnd(e.target.value)}
                    className="w-full text-xs p-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Evidence Submission Due Date</label>
                <input
                  type="date"
                  required
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="p-3 bg-blue-50/70 rounded-lg border border-blue-200 text-xs text-blue-800">
                ⚡ Automatically generates an evidence request code (e.g. <code>REQ-2026-XXXX</code>) and prepares email notification for the scope owner.
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Initiating...' : 'Initiate Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
