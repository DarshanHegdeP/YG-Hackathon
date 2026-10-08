import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './layouts/AppLayout';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ControlsPage } from './pages/ControlsPage';
import { ControlDetailPage } from './pages/ControlDetailPage';
import { ScopesPage } from './pages/ScopesPage';
import { AssignmentsPage } from './pages/AssignmentsPage';
import { ReviewsPage } from './pages/ReviewsPage';
import { ReviewDetailPage } from './pages/ReviewDetailPage';
import { EvidenceRequestsPage } from './pages/EvidenceRequestsPage';
import { EvidenceRequestDetailPage } from './pages/EvidenceRequestDetailPage';
import { PublicSubmissionPage } from './pages/PublicSubmissionPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const ReviewerOnlyRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-slate-500">Loading session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'REVIEWER') return <Navigate to="/dashboard" replace />;
  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/submit/:secureToken" element={<PublicSubmissionPage />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route
              path="/controls"
              element={<ReviewerOnlyRoute><ControlsPage /></ReviewerOnlyRoute>}
            />
            <Route
              path="/controls/:id"
              element={<ReviewerOnlyRoute><ControlDetailPage /></ReviewerOnlyRoute>}
            />
            <Route
              path="/scopes"
              element={<ReviewerOnlyRoute><ScopesPage /></ReviewerOnlyRoute>}
            />
            <Route
              path="/assignments"
              element={<ReviewerOnlyRoute><AssignmentsPage /></ReviewerOnlyRoute>}
            />
            <Route path="/reviews" element={<ReviewsPage />} />
            <Route path="/reviews/:id" element={<ReviewDetailPage />} />
            <Route path="/evidence-requests" element={<EvidenceRequestsPage />} />
            <Route path="/evidence-requests/:id" element={<EvidenceRequestDetailPage />} />
            <Route
              path="/audit-logs"
              element={<ReviewerOnlyRoute><AuditLogsPage /></ReviewerOnlyRoute>}
            />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
