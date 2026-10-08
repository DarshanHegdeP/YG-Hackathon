import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  UploadCloud,
  FileCheck2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Shield,
  FileText,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { requestsAPI, evidenceAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { AIValidationCard } from '../components/AIValidationCard';

export const PublicSubmissionPage = () => {
  const { secureToken } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await requestsAPI.getByToken(secureToken);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [secureToken]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadError('');
      setUploadSuccess('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a valid document to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('secure_token', secureToken);

    try {
      setUploading(true);
      setUploadError('');
      setUploadSuccess('');
      await evidenceAPI.upload(formData);
      setUploadSuccess('File uploaded successfully! Automated Gemini AI verification completed.');
      setSelectedFile(null);
      await loadData();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
        <div className="text-slate-500 flex items-center space-x-2 text-sm">
          <span>Loading secure submission portal...</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 max-w-md text-center shadow-lg">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900">Submission Link Expired or Invalid</h2>
          <p className="text-xs text-slate-500 mt-2">
            The requested evidence token was not found. Please verify the link in your email notification or contact your compliance reviewer.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md">
                <Shield className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold tracking-wider text-blue-400 uppercase">
                  LOD2 Compliance Testing
                </span>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
                  Evidence Submission Portal
                </h1>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-sm bg-slate-800 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 block sm:inline-block">
                {data.request_code}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-800 text-xs text-slate-300">
            <div>
              <span className="text-slate-400 block">Control:</span>
              <strong className="text-white text-sm">{data.control_code}</strong> — {data.control_name}
            </div>
            <div>
              <span className="text-slate-400 block">Scope Target:</span>
              <strong className="text-white text-sm">{data.scope_name}</strong> ({data.scope_type})
            </div>
            <div>
              <span className="text-slate-400 block">Submission Deadline:</span>
              <span className="text-rose-400 font-bold text-sm">
                {new Date(data.due_date).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        {/* Requirements Box */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Required Evidence Items</h3>
              <p className="text-xs text-slate-500">
                Period: {new Date(data.period_start).toLocaleDateString()} to {new Date(data.period_end).toLocaleDateString()}
              </p>
            </div>
            <StatusBadge status={data.status} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
            {data.required_evidence?.map((req) => (
              <div key={req.id} className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
                <div>
                  <span className="font-bold text-slate-800">{req.name}</span>
                  {req.description && <p className="text-[11px] text-slate-500 mt-0.5">{req.description}</p>}
                </div>
              </div>
            ))}
          </div>

          {/* Upload Zone */}
          <form onSubmit={handleUpload} className="mt-6 pt-6 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
              Upload Evidence Document
            </h4>
            <p className="text-xs text-slate-500 mb-3">
              Supported formats: <strong>PDF, XLSX, DOCX, CSV</strong> (Max 25 MB). Files are cryptographically hashed with SHA-256 and evaluated by Gemini AI.
            </p>

            {uploadError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                {uploadError}
              </div>
            )}

            {uploadSuccess && (
              <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium">
                {uploadSuccess}
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                type="file"
                accept=".pdf,.xlsx,.xls,.docx,.csv,.txt"
                onChange={handleFileChange}
                className="block w-full text-xs text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer border border-slate-200 rounded-xl p-1 bg-slate-50"
              />
              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md transition-all disabled:opacity-50 shrink-0"
              >
                <UploadCloud className="w-4 h-4" />
                <span>{uploading ? 'Processing & Validating...' : 'Upload & Verify'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* AI Validation Feedback */}
        {data.latest_validation && (
          <AIValidationCard validation={data.latest_validation} />
        )}

        {/* List of previously uploaded files */}
        {data.uploaded_evidences && data.uploaded_evidences.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Uploaded Files History</h3>
            <div className="divide-y divide-slate-100">
              {data.uploaded_evidences.map((ev) => (
                <div key={ev.id} className="py-2.5 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2.5">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <div>
                      <span className="font-semibold text-slate-800">{ev.file_name}</span>
                      <span className="text-slate-400 text-[11px] ml-2">({(ev.file_size / 1024).toFixed(1)} KB)</span>
                    </div>
                  </div>
                  <StatusBadge status={ev.processing_status} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
