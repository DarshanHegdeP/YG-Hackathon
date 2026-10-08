import React from 'react';
import { Mail, Clock, AlertTriangle, CheckCircle2, FileUp, Sparkles, Send } from 'lucide-react';

export const Timeline = ({ communications = [], evidences = [] }) => {
  // Merge communications and evidence uploads into a single ordered timeline
  const events = [];

  communications.forEach((comm) => {
    events.push({
      id: `comm-${comm.id}`,
      type: 'COMMUNICATION',
      subType: comm.type,
      title: comm.subject,
      subtitle: `Recipient: ${comm.recipient}`,
      timestamp: new Date(comm.sent_at),
      status: comm.status,
      metadata: comm.metadata_json,
    });
  });

  evidences.forEach((ev) => {
    events.push({
      id: `ev-${ev.id}`,
      type: 'EVIDENCE_UPLOAD',
      subType: ev.processing_status,
      title: `Evidence Uploaded: ${ev.file_name}`,
      subtitle: `Size: ${(ev.file_size / 1024).toFixed(1)} KB | SHA-256: ${ev.sha256.substring(0, 12)}...`,
      timestamp: new Date(ev.uploaded_at),
      validations: ev.validations || [],
    });
  });

  events.sort((a, b) => b.timestamp - a.timestamp);

  const getEventIcon = (event) => {
    if (event.type === 'EVIDENCE_UPLOAD') {
      return <FileUp className="w-4 h-4 text-purple-600" />;
    }
    switch (event.subType) {
      case 'INITIAL_REQUEST':
        return <Send className="w-4 h-4 text-blue-600" />;
      case 'REMINDER_1':
      case 'REMINDER_2':
        return <Clock className="w-4 h-4 text-amber-600" />;
      case 'FINAL_REMINDER':
        return <AlertTriangle className="w-4 h-4 text-rose-600" />;
      case 'MISSING_EVIDENCE':
        return <AlertTriangle className="w-4 h-4 text-orange-600" />;
      case 'ESCALATION':
        return <AlertTriangle className="w-4 h-4 text-red-700" />;
      case 'COMPLETION':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      default:
        return <Mail className="w-4 h-4 text-slate-600" />;
    }
  };

  const getBadgeStyle = (event) => {
    if (event.type === 'EVIDENCE_UPLOAD') {
      return 'bg-purple-100 border-purple-200 text-purple-800';
    }
    switch (event.subType) {
      case 'INITIAL_REQUEST':
        return 'bg-blue-100 border-blue-200 text-blue-800';
      case 'REMINDER_1':
      case 'REMINDER_2':
        return 'bg-amber-100 border-amber-200 text-amber-800';
      case 'FINAL_REMINDER':
        return 'bg-rose-100 border-rose-200 text-rose-800';
      case 'MISSING_EVIDENCE':
        return 'bg-orange-100 border-orange-200 text-orange-800';
      case 'ESCALATION':
        return 'bg-red-100 border-red-200 text-red-800';
      case 'COMPLETION':
        return 'bg-emerald-100 border-emerald-200 text-emerald-800';
      default:
        return 'bg-slate-100 border-slate-200 text-slate-800';
    }
  };

  if (events.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-400 bg-white rounded-xl border border-slate-200">
        No communication or upload history recorded yet.
      </div>
    );
  }

  return (
    <div className="flow-root bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
      <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-5 flex items-center space-x-2">
        <Clock className="w-4 h-4 text-blue-600" />
        <span>Communication & Verification Timeline</span>
      </h3>
      <ul className="-mb-8">
        {events.map((event, eventIdx) => (
          <li key={event.id}>
            <div className="relative pb-8">
              {eventIdx !== events.length - 1 ? (
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200" aria-hidden="true" />
              ) : null}
              <div className="relative flex space-x-3 items-start">
                <div>
                  <span className="h-8 w-8 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center ring-4 ring-white shadow-xs">
                    {getEventIcon(event)}
                  </span>
                </div>
                <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getBadgeStyle(event)}`}>
                        {event.subType}
                      </span>
                      <p className="text-sm font-semibold text-slate-900">{event.title}</p>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{event.subtitle}</p>

                    {/* Missing items pill */}
                    {event.metadata?.missing_items && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <span className="text-[11px] font-semibold text-orange-800">Missing:</span>
                        {event.metadata.missing_items.map((item, i) => (
                          <span key={i} className="text-[11px] bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-200">
                            {item}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* AI validation on upload */}
                    {event.validations && event.validations.length > 0 && (
                      <div className="mt-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                        <div className="flex items-center space-x-1.5 font-semibold text-slate-700">
                          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                          <span>AI Assessment Result: {event.validations[0].status}</span>
                          <span className="text-slate-400 font-normal">({Math.round(event.validations[0].confidence * 100)}% confidence)</span>
                        </div>
                        <p className="text-slate-600 mt-1">{event.validations[0].reason}</p>
                      </div>
                    )}
                  </div>
                  <div className="text-right text-xs whitespace-nowrap text-slate-400">
                    <time dateTime={event.timestamp.toISOString()}>
                      {event.timestamp.toLocaleDateString()} {event.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </time>
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
