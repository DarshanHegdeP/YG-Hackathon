import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { controlsAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { ArrowLeft, CheckCircle2, ShieldCheck } from 'lucide-react';

export const ControlDetailPage = () => {
  const { id } = useParams();
  const [control, setControl] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchControl = async () => {
      try {
        const res = await controlsAPI.get(id);
        setControl(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchControl();
  }, [id]);

  if (loading || !control) {
    return <div className="p-8 text-center text-slate-500">Loading control details...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/controls" className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-800">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Controls Registry</span>
      </Link>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <span className="text-xl font-bold font-mono text-blue-600 bg-blue-50 px-3 py-1 rounded-lg border border-blue-200">
              {control.control_code}
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-900">{control.name}</h1>
              <p className="text-xs text-slate-500">Frequency: {control.frequency}</p>
            </div>
          </div>
          <StatusBadge status={control.status} />
        </div>

        <div className="mt-5 space-y-4">
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Control Description & Objective</h4>
            <p className="text-sm text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200 leading-relaxed">
              {control.description}
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Mandatory & Optional Evidence Requirements</h4>
            <div className="space-y-2">
              {control.evidence_requirements?.map((req) => (
                <div key={req.id} className="flex items-start justify-between p-3 rounded-lg border border-slate-200 bg-white">
                  <div className="flex items-start space-x-2.5">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-slate-800">{req.name}</span>
                      {req.description && (
                        <p className="text-[11px] text-slate-500 mt-0.5">{req.description}</p>
                      )}
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${req.mandatory ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-100 text-slate-600'}`}>
                    {req.mandatory ? 'MANDATORY' : 'OPTIONAL'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
