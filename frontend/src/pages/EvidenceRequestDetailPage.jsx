import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Bell,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  ExternalLink,
  FileText,
  FileCheck2,
  RefreshCw,
  Mail,
  Clock,
  Sparkles,
  Download
} from 'lucide-react';
import { requestsAPI, evidenceAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { AIValidationCard } from '../components/AIValidationCard';
import { Timeline } from '../components/Timeline';
import { useAuth } from '../context/AuthContext';

export const EvidenceRequestDetailPage = () => {
  const { id } = useParams();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);
  const [showExtractedModal, setShowExtractedModal] = useState(null);
  const [newDueDate, setNewDueDate] = useState('');
  const [showExtendModal, setShowExtendModal] = useState(false);
  const { isReviewer } = useAuth();

  const loadRequest = async () => {
    try {
      setLoading(true);
      const res = await requestsAPI.get(id);
      setRequest(res.data);
      if (res.data?.due_date) {
        setNewDueDate(res.data.due_date.split('T')[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequest();
  }, [id]);

  const handleSendReminder = async () => {
    try {
      setActionLoading(true);
      await requestsAPI.remind(id);
      setActionMsg('Automated reminder email sent and communication logged.');
      await loadRequest();
    } catch (err) {
      setActionMsg('Failed to send reminder.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    try {
      setActionLoading(true);
      await requestsAPI.escalate(id);
      setActionMsg('Escalation notice sent to designated escalation contact.');
      await loadRequest();
    } catch (err) {
      setActionMsg('Failed to send escalation.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkComplete = async () => {
    try {
      setActionLoading(true);
      await requestsAPI.markComplete(id);
      setActionMsg('Evidence request marked as COMPLETE. Acceptance email dispatched.');
      await loadRequest();
    } catch (err) {
      setActionMsg('Failed to mark complete.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExtendDueDate = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      await requestsAPI.update(id, { due_date: new Date(newDueDate).toISOString() });
      setShowExtendModal(false);
      setActionMsg(`Due date extended to ${newDueDate}.`);
      await loadRequest();
    } catch (err) {
      setActionMsg('Failed to extend due date.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevalidate = async (evidenceId) => {
    try {
      setActionLoading(true);
      await evidenceAPI.revalidate(evidenceId);
      setActionMsg('AI validation re-evaluated.');
      await loadRequest();
    } catch (err) {
      setActionMsg('Failed to revalidate evidence.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading || !request) {
    return <div className="p-8 text-center text-slate-500">Loading evidence request details...</div>;
  }

  const review = request.review;
  const assignment = review?.assignment;
  const control = assignment?.control;
  const scope = assignment?.scope;
  const latestEvidence = request.evidences && request.evidences.length > 0
    ? request.evidences[request.evidences.length - 1]
    : null;
  const latestValidation = latestEvidence?.validations && latestEvidence.validations.length > 0
    ? latestEvidence.validations[latestEvidence.validations.length - 1]
    : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/evidence-requests" className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-800">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Evidence Requests</span>
        </Link>

        <a
          href={`/submit/${request.secure_token}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 border border-blue-200 transition-colors shadow-2xs"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          <span>Open Recipient Submission Page</span>
        </a>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 text-xs flex items-center justify-between shadow-2xs">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-3">
              <span className="font-mono font-bold text-slate-900 text-xl tracking-tight">
                {request.request_code}
              </span>
              <StatusBadge status={request.status} className="text-xs px-2.5 py-1" />
            </div>
            <p className="text-sm font-semibold text-slate-800 mt-1">
              {control?.control_code} — {control?.name}
            </p>
            <p className="text-xs text-slate-500">
              Scope: <strong>{scope?.name}</strong> ({scope?.type}) | Recipient: <span className="font-mono">{scope?.email}</span>
            </p>
          </div>

          {/* Action Buttons */}
          {isReviewer && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleSendReminder}
                disabled={actionLoading}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold border border-slate-200 transition-colors disabled:opacity-50"
              >
                <Bell className="w-3.5 h-3.5 text-blue-600" />
                <span>Send Reminder</span>
              </button>

              <button
                onClick={() => setShowExtendModal(true)}
                disabled={actionLoading}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold border border-slate-200 transition-colors disabled:opacity-50"
              >
                <Calendar className="w-3.5 h-3.5 text-slate-600" />
                <span>Extend Due Date</span>
              </button>

              <button
                onClick={handleEscalate}
                disabled={actionLoading}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold border border-rose-200 transition-colors disabled:opacity-50"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                <span>Escalate</span>
              </button>

              {request.status !== 'COMPLETE' && (
                <button
                  onClick={handleMarkComplete}
                  disabled={actionLoading}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Mark Complete</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* 4 Details Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 block font-medium">Review Period</span>
            <span className="font-bold text-slate-800 mt-0.5 block">
              {review ? `${new Date(review.period_start).toLocaleDateString()} – ${new Date(review.period_end).toLocaleDateString()}` : 'N/A'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 block font-medium">Submission Due Date</span>
            <span className="font-bold text-slate-800 mt-0.5 block">
              {new Date(request.due_date).toLocaleDateString()}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 block font-medium">Reminders Sent</span>
            <span className="font-bold text-slate-800 mt-0.5 block">
              {request.reminder_count} reminders logged
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 block font-medium">Evidence Submissions</span>
            <span className="font-bold text-slate-800 mt-0.5 block">
              {request.evidences?.length || 0} files received
            </span>
          </div>
        </div>

        {/* Required Evidence Checklist */}
        <div>
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
            Required Control Evidence Checklist
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {control?.evidence_requirements?.map((req) => (
              <div key={req.id} className="p-3 rounded-lg border border-slate-200 bg-white flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-800">{req.name}</span>
                  {req.description && <p className="text-[11px] text-slate-500">{req.description}</p>}
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${req.mandatory ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-100 text-slate-600'}`}>
                  {req.mandatory ? 'MANDATORY' : 'OPTIONAL'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Validation Card */}
      <AIValidationCard validation={latestValidation} />

      {/* Uploaded Files Table */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center space-x-2">
          <FileCheck2 className="w-4 h-4 text-blue-600" />
          <span>Uploaded Evidence Documents</span>
        </h3>

        {(!request.evidences || request.evidences.length === 0) ? (
          <div className="p-8 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl">
            No evidence documents uploaded yet for this request.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {request.evidences.map((ev) => (
              <div key={ev.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-200 mt-0.5">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900">{ev.file_name}</div>
                    <div className="text-[11px] text-slate-500 flex items-center space-x-2 mt-0.5">
                      <span>Size: {(ev.file_size / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span>Format: {ev.file_type}</span>
                      <span>•</span>
                      <span className="font-mono text-[10px]">SHA-256: {ev.sha256}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end sm:self-center">
                  <StatusBadge status={ev.processing_status} />

                  {ev.extracted_text && (
                    <button
                      onClick={() => setShowExtractedModal(ev)}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800 px-2 py-1 bg-slate-50 rounded border border-slate-200"
                    >
                      View Extracted Text
                    </button>
                  )}

                  {isReviewer && (
                    <button
                      onClick={() => handleRevalidate(ev.id)}
                      disabled={actionLoading}
                      className="text-xs font-semibold text-slate-600 hover:text-slate-900 px-2 py-1 bg-slate-50 rounded border border-slate-200"
                    >
                      Re-run AI
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Communications & Event Timeline */}
      <Timeline
        communications={request.communications || []}
        evidences={request.evidences || []}
      />

      {/* Modal: View Extracted Text */}
      {showExtractedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-6 shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h4 className="text-sm font-bold text-slate-900">Extracted Structured Content</h4>
                <p className="text-xs text-slate-500">{showExtractedModal.file_name} (SHA-256: {showExtractedModal.sha256.substring(0, 16)}...)</p>
              </div>
              <button
                onClick={() => setShowExtractedModal(null)}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto my-4 p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs whitespace-pre-wrap">
              {showExtractedModal.extracted_text || 'No text extracted.'}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowExtractedModal(null)}
                className="px-4 py-1.5 text-xs font-semibold bg-slate-800 text-white rounded-lg hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Extend Due Date */}
      {showExtendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h4 className="text-sm font-bold text-slate-900 mb-1">Extend Evidence Due Date</h4>
            <p className="text-xs text-slate-500 mb-4">Set a new submission deadline for request {request.request_code}.</p>
            <form onSubmit={handleExtendDueDate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Due Date</label>
                <input
                  type="date"
                  required
                  value={newDueDate}
                  onChange={(e) => setNewDueDate(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowExtendModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-3.5 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Confirm Extension
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
