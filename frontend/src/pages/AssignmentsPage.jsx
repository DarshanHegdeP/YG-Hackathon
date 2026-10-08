import React, { useState, useEffect } from 'react';
import { Plus, Search, FileCheck2, ShieldCheck, Target, User } from 'lucide-react';
import { assignmentsAPI, controlsAPI, scopesAPI, authAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const AssignmentsPage = () => {
  const [assignments, setAssignments] = useState([]);
  const [controls, setControls] = useState([]);
  const [scopes, setScopes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const { isReviewer, user } = useAuth();

  // Form state
  const [controlId, setControlId] = useState('');
  const [scopeId, setScopeId] = useState('');
  const [freq, setFreq] = useState('QUARTERLY');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [assignRes, ctrlRes, scRes] = await Promise.all([
        assignmentsAPI.list(),
        controlsAPI.list(),
        scopesAPI.list(),
      ]);
      setAssignments(assignRes.data);
      setControls(ctrlRes.data);
      setScopes(scRes.data);
      if (ctrlRes.data.length > 0) setControlId(ctrlRes.data[0].id);
      if (scRes.data.length > 0) setScopeId(scRes.data[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await assignmentsAPI.create({
        control_id: parseInt(controlId),
        scope_id: parseInt(scopeId),
        reviewer_id: user?.id || 1,
        frequency: freq,
        effective_from: new Date().toISOString(),
        status: 'ACTIVE'
      });
      setShowModal(false);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create control assignment.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Control Assignments</h1>
          <p className="text-sm text-slate-500 mt-1">
            Map reusable LOD2 controls to specific organizational scopes and reviewers
          </p>
        </div>

        {isReviewer && (
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Assign Control to Scope</span>
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-5 py-3">Control</th>
              <th className="px-5 py-3">Assigned Scope Target</th>
              <th className="px-5 py-3">Designated Reviewer</th>
              <th className="px-5 py-3">Testing Frequency</th>
              <th className="px-5 py-3">Effective Date</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {assignments.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-5 py-8 text-center text-slate-400">
                  {loading ? 'Loading assignments...' : 'No assignments configured.'}
                </td>
              </tr>
            ) : (
              assignments.map((as) => (
                <tr key={as.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="font-bold font-mono text-blue-600">{as.control?.control_code}</div>
                    <div className="font-semibold text-slate-800">{as.control?.name}</div>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="font-semibold text-slate-900">{as.scope?.name}</div>
                    <div className="text-slate-400 text-[11px]">({as.scope?.type}) - {as.scope?.email}</div>
                  </td>
                  <td className="px-5 py-3.5 text-slate-700">
                    <div className="font-medium">{as.reviewer?.name || 'Reviewer'}</div>
                    <div className="text-slate-400 text-[11px] font-mono">{as.reviewer?.email}</div>
                  </td>
                  <td className="px-5 py-3.5 font-medium text-slate-600">
                    {as.frequency}
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {new Date(as.effective_from).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={as.status} />
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
            <h3 className="text-lg font-bold text-slate-900 mb-1">Create Control Assignment</h3>
            <p className="text-xs text-slate-500 mb-4">Connect a reusable control to an evidence scope target.</p>

            {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-xs rounded-lg">{error}</div>}

            <form onSubmit={handleCreateAssignment} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Control</label>
                <select
                  value={controlId}
                  onChange={(e) => setControlId(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  {controls.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.control_code} - {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Scope Target</label>
                <select
                  value={scopeId}
                  onChange={(e) => setScopeId(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  {scopes.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.type}) - {s.email}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Testing Frequency</label>
                <select
                  value={freq}
                  onChange={(e) => setFreq(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="MONTHLY">MONTHLY</option>
                  <option value="QUARTERLY">QUARTERLY</option>
                  <option value="SEMI_ANNUAL">SEMI_ANNUAL</option>
                  <option value="ANNUAL">ANNUAL</option>
                  <option value="AD_HOC">AD_HOC</option>
                </select>
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
                  {submitting ? 'Assigning...' : 'Confirm Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
