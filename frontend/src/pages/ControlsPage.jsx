import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, ShieldCheck, Check, Trash2 } from 'lucide-react';
import { controlsAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const ControlsPage = () => {
  const [controls, setControls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const { isReviewer } = useAuth();

  // New control form state
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [freq, setFreq] = useState('QUARTERLY');
  const [requirements, setRequirements] = useState([
    { name: 'Access Review Report', description: 'Listing of accounts', mandatory: true },
    { name: 'Reviewer Confirmation', description: 'Manager attestation', mandatory: true }
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadControls = async () => {
    try {
      setLoading(true);
      const res = await controlsAPI.list({ search: search || undefined });
      setControls(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadControls();
  }, [search]);

  const handleAddRequirement = () => {
    setRequirements([...requirements, { name: '', description: '', mandatory: true }]);
  };

  const handleRemoveRequirement = (idx) => {
    setRequirements(requirements.filter((_, i) => i !== idx));
  };

  const handleReqChange = (idx, field, val) => {
    const updated = [...requirements];
    updated[idx][field] = val;
    setRequirements(updated);
  };

  const handleCreateControl = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await controlsAPI.create({
        control_code: code,
        name,
        description: desc,
        frequency: freq,
        status: 'ACTIVE',
        requirements: requirements.filter(r => r.name.trim() !== '')
      });
      setShowModal(false);
      setCode('');
      setName('');
      setDesc('');
      loadControls();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create control.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Internal Controls Registry</h1>
          <p className="text-sm text-slate-500 mt-1">
            Reusable LOD2 controls and required evidence definitions
          </p>
        </div>

        {isReviewer && (
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Control</span>
          </button>
        )}
      </div>

      <div className="flex items-center bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
        <Search className="w-4 h-4 text-slate-400 ml-1" />
        <input
          type="text"
          placeholder="Search controls by code, name, or description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-transparent border-none text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden pl-3"
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-5 py-3">Control Code</th>
              <th className="px-5 py-3">Control Name</th>
              <th className="px-5 py-3">Frequency</th>
              <th className="px-5 py-3">Requirements</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {controls.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-5 py-8 text-center text-slate-400">
                  {loading ? 'Loading controls...' : 'No controls found.'}
                </td>
              </tr>
            ) : (
              controls.map((ctrl) => (
                <tr key={ctrl.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5 font-bold font-mono text-blue-600">
                    {ctrl.control_code}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="font-semibold text-slate-900">{ctrl.name}</div>
                    <div className="text-slate-500 text-[11px] truncate max-w-md">{ctrl.description}</div>
                  </td>
                  <td className="px-5 py-3.5 font-medium text-slate-600">
                    {ctrl.frequency}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded text-[11px]">
                      {ctrl.evidence_requirements?.length || 0} items
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={ctrl.status} />
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <Link
                      to={`/controls/${ctrl.id}`}
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

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Create New Control</h3>
            <p className="text-xs text-slate-500 mb-4">Define reusable control and required evidence checklist.</p>

            {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-xs rounded-lg">{error}</div>}

            <form onSubmit={handleCreateControl} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Control Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. C003"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Frequency</label>
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
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Control Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Vulnerability Remediation SLA Testing"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Control Description</label>
                <textarea
                  rows="2"
                  required
                  placeholder="Detailed control objective and audit criteria..."
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-bold text-slate-800">Required Evidence Items</label>
                  <button
                    type="button"
                    onClick={handleAddRequirement}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                  >
                    + Add Item
                  </button>
                </div>

                <div className="space-y-2">
                  {requirements.map((req, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Requirement name (e.g. Scan Report)"
                        value={req.name}
                        onChange={(e) => handleReqChange(idx, 'name', e.target.value)}
                        className="flex-1 text-xs p-1.5 border border-slate-300 rounded-lg"
                      />
                      <label className="flex items-center space-x-1 text-[11px] text-slate-600">
                        <input
                          type="checkbox"
                          checked={req.mandatory}
                          onChange={(e) => handleReqChange(idx, 'mandatory', e.target.checked)}
                        />
                        <span>Mandatory</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => handleRemoveRequirement(idx)}
                        className="text-slate-400 hover:text-red-500"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
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
                  {submitting ? 'Creating...' : 'Save Control'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
