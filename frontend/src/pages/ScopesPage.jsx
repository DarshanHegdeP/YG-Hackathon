import React, { useState, useEffect } from 'react';
import { Target, Plus, Search, Mail, UserCheck, AlertTriangle } from 'lucide-react';
import { scopesAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const ScopesPage = () => {
  const [scopes, setScopes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const { isReviewer } = useAuth();

  // Form state
  const [type, setType] = useState('TEAM');
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadScopes = async () => {
    try {
      setLoading(true);
      const res = await scopesAPI.list({
        type: typeFilter || undefined,
        search: search || undefined
      });
      setScopes(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScopes();
  }, [typeFilter, search]);

  const handleCreateScope = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await scopesAPI.create({
        type,
        name,
        description: desc,
        email,
      });
      setShowModal(false);
      setName('');
      setDesc('');
      setEmail('');
      loadScopes();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create scope.');
    } finally {
      setSubmitting(false);
    }
  };

  const scopeTypeBadge = (t) => {
    const map = {
      PERSON: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      TEAM: 'bg-blue-50 text-blue-700 border-blue-200',
      DEPARTMENT: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      BUSINESS_UNIT: 'bg-purple-50 text-purple-700 border-purple-200',
      APPLICATION: 'bg-amber-50 text-amber-700 border-amber-200',
      SYSTEM_OWNER: 'bg-rose-50 text-rose-700 border-rose-200',
      OTHER: 'bg-slate-100 text-slate-700 border-slate-200',
    };
    return (
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${map[t] || map.OTHER}`}>
        {t}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Scope & Contact Directory</h1>
          <p className="text-sm text-slate-500 mt-1">
            Dynamic evidence provider targets (Persons, Teams, Departments, Applications, System Owners)
          </p>
        </div>

        {isReviewer && (
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Scope</span>
          </button>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 flex items-center bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
          <Search className="w-4 h-4 text-slate-400 ml-1" />
          <input
            type="text"
            placeholder="Search scopes by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-transparent border-none text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden pl-3"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="bg-white px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 shadow-xs"
        >
          <option value="">All Scope Types</option>
          <option value="PERSON">PERSON</option>
          <option value="TEAM">TEAM</option>
          <option value="DEPARTMENT">DEPARTMENT</option>
          <option value="BUSINESS_UNIT">BUSINESS_UNIT</option>
          <option value="APPLICATION">APPLICATION</option>
          <option value="SYSTEM_OWNER">SYSTEM_OWNER</option>
          <option value="OTHER">OTHER</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-5 py-3">Scope Name</th>
              <th className="px-5 py-3">Type</th>
              <th className="px-5 py-3">Target Email</th>
              <th className="px-5 py-3">Owner / Contact</th>
              <th className="px-5 py-3">Escalation Contact</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {scopes.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-5 py-8 text-center text-slate-400">
                  {loading ? 'Loading scopes...' : 'No scopes registered.'}
                </td>
              </tr>
            ) : (
              scopes.map((sc) => (
                <tr key={sc.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="font-semibold text-slate-900">{sc.name}</div>
                    {sc.description && <div className="text-slate-400 text-[11px]">{sc.description}</div>}
                  </td>
                  <td className="px-5 py-3.5">
                    {scopeTypeBadge(sc.type)}
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-700">
                    <div className="flex items-center space-x-1.5">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span>{sc.email}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    {sc.owner_name || 'Assigned Lead'}
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    {sc.escalation_name || 'Designated Escalation'}
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
            <h3 className="text-lg font-bold text-slate-900 mb-1">Create Scope Target</h3>
            <p className="text-xs text-slate-500 mb-4">Register a person, team, or application responsible for evidence.</p>

            {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-xs rounded-lg">{error}</div>}

            <form onSubmit={handleCreateScope} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Scope Type</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="TEAM">TEAM</option>
                  <option value="PERSON">PERSON</option>
                  <option value="DEPARTMENT">DEPARTMENT</option>
                  <option value="BUSINESS_UNIT">BUSINESS_UNIT</option>
                  <option value="APPLICATION">APPLICATION</option>
                  <option value="SYSTEM_OWNER">SYSTEM_OWNER</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Scope Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Core Banking Application"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Evidence Recipient Email</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. app-leads@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows="2"
                  placeholder="Notes regarding this scope or ownership..."
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
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
                  {submitting ? 'Creating...' : 'Save Scope'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
