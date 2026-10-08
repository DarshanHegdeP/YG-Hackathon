import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { reviewsAPI } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { ArrowLeft, Inbox, ChevronRight, Calendar } from 'lucide-react';

export const ReviewDetailPage = () => {
  const { id } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReview = async () => {
      try {
        const res = await reviewsAPI.get(id);
        setReview(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchReview();
  }, [id]);

  if (loading || !review) {
    return <div className="p-8 text-center text-slate-500">Loading review details...</div>;
  }

  const ctrl = review.assignment?.control;
  const scope = review.assignment?.scope;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/reviews" className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-800">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Review Cycles</span>
      </Link>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold font-mono text-blue-600 text-lg">{ctrl?.control_code}</span>
              <h1 className="text-lg font-bold text-slate-900">{ctrl?.name}</h1>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Assigned Scope: <strong>{scope?.name}</strong> ({scope?.email})</p>
          </div>
          <StatusBadge status={review.status} />
        </div>

        <div className="grid grid-cols-3 gap-4 my-5 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
          <div>
            <span className="text-slate-500 block">Period Covered</span>
            <span className="font-semibold text-slate-800">
              {new Date(review.period_start).toLocaleDateString()} to {new Date(review.period_end).toLocaleDateString()}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Due Date</span>
            <span className="font-semibold text-slate-800">
              {new Date(review.due_date).toLocaleDateString()}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Assigned Reviewer</span>
            <span className="font-semibold text-slate-800">
              {review.assignment?.reviewer?.name || 'Reviewer'}
            </span>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-2">
            <Inbox className="w-4 h-4 text-blue-600" />
            <span>Associated Evidence Requests</span>
          </h3>

          <div className="space-y-2">
            {review.evidence_requests?.map((req) => (
              <div key={req.id} className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
                <div>
                  <span className="font-mono font-bold text-slate-900 text-xs">{req.request_code}</span>
                  <div className="text-[11px] text-slate-500 mt-0.5">Due: {new Date(req.due_date).toLocaleDateString()} | Reminders: {req.reminder_count}</div>
                </div>
                <div className="flex items-center space-x-3">
                  <StatusBadge status={req.status} />
                  <Link
                    to={`/evidence-requests/${req.id}`}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
