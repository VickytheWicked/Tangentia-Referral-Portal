import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { EmployeeDashboard } from './pages/employee/EmployeeDashboard';
import { SubmitReferralPage } from './pages/employee/SubmitReferralPage';
import { MyReferralsPage } from './pages/employee/MyReferralsPage';
import { HRDashboard } from './pages/hr/HRDashboard';
import { AllReferralsPage } from './pages/hr/AllReferralsPage';
import { JobPositionsPage } from './pages/hr/JobPositionsPage';
import { AnalyticsPage } from './pages/hr/AnalyticsPage';
import { OpeningsPage } from './pages/employee/OpeningsPage';
import { HiredHistoryPage } from './pages/common/HiredHistoryPage';
import { LoginPage } from './pages/Login';
import { HRSuggestionsPage } from './pages/hr/HRSuggestionsPage';

// Protected Route wrapper ensuring only authenticated HR users access HR Administration
const RequireHR: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isHR, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '60vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-secondary)',
          fontSize: '0.95rem',
        }}
      >
        Verifying HR credentials...
      </div>
    );
  }

  if (!isHR) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

const MainPortalContent: React.FC = () => {
  const { isLoading } = useAuth();
  const navigate = useNavigate();
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-main)',
          color: 'var(--text-secondary)',
          fontSize: '1rem',
        }}
      >
        Initializing Tangentia Portal...
      </div>
    );
  }

  const handleOpenCandidate = (candidateId: string) => {
    setSelectedCandidateId(candidateId);
    navigate('/hr/referrals');
  };

  const routes = (
    <Routes>
      {/* Default Landing -> Redirects directly to Employee Dashboard (No Login Needed) */}
      <Route path="/" element={<Navigate to="/employee/dashboard" replace />} />

      {/* HR Login Page */}
      <Route path="/login" element={<LoginPage />} />

      {/* ================================================================ */}
      {/* Employee Workspace Routes (Fully Public - No Login Required)     */}
      {/* ================================================================ */}
      <Route path="/employee" element={<Navigate to="/employee/dashboard" replace />} />
      <Route
        path="/employee/dashboard"
        element={
          <EmployeeDashboard
            onNavigate={(tab) => {
              if (tab === 'submit-referral') navigate('/employee/submit');
              else if (tab === 'my-referrals' || tab === 'referrals') navigate('/employee/referrals');
              else if (tab === 'openings') navigate('/employee/openings');
              else if (tab === 'hired-history') navigate('/employee/hired-history');
            }}
          />
        }
      />
      <Route
        path="/employee/submit"
        element={
          <SubmitReferralPage
            onReferralCreated={() => navigate('/employee/referrals')}
          />
        }
      />
      <Route path="/employee/openings" element={<OpeningsPage />} />
      <Route path="/employee/hired-history" element={<HiredHistoryPage />} />
      <Route
        path="/employee/referrals"
        element={
          <MyReferralsPage
            onNavigate={(tab) => {
              if (tab === 'submit-referral') navigate('/employee/submit');
              else if (tab === 'employee-dashboard') navigate('/employee/dashboard');
            }}
          />
        }
      />
      <Route path="/employee/my-referrals" element={<Navigate to="/employee/referrals" replace />} />

      {/* ================================================================ */}
      {/* HR Administration Hub Routes (Protected - HR Login Required)    */}
      {/* ================================================================ */}
      <Route path="/hr" element={<Navigate to="/hr/dashboard" replace />} />
      <Route
        path="/hr/dashboard"
        element={
          <RequireHR>
            <HRDashboard
              onNavigate={(tab) => {
                if (tab === 'all-referrals') navigate('/hr/referrals');
                else if (tab === 'job-positions') navigate('/hr/jobs');
                else if (tab === 'analytics') navigate('/hr/analytics');
                else if (tab === 'hired-history') navigate('/hr/hired-history');
              }}
              onOpenCandidate={handleOpenCandidate}
            />
          </RequireHR>
        }
      />
      <Route
        path="/hr/referrals"
        element={
          <RequireHR>
            <AllReferralsPage
              initialSelectedId={selectedCandidateId}
              onClearInitialId={() => setSelectedCandidateId(null)}
            />
          </RequireHR>
        }
      />
      <Route
        path="/hr/suggestions"
        element={
          <RequireHR>
            <HRSuggestionsPage />
          </RequireHR>
        }
      />
      <Route
        path="/hr/jobs"
        element={
          <RequireHR>
            <JobPositionsPage />
          </RequireHR>
        }
      />
      <Route
        path="/hr/analytics"
        element={
          <RequireHR>
            <AnalyticsPage />
          </RequireHR>
        }
      />
      <Route
        path="/hr/hired-history"
        element={
          <RequireHR>
            <HiredHistoryPage />
          </RequireHR>
        }
      />

      {/* Catch-all fallback -> Redirects to Employee Dashboard */}
      <Route path="*" element={<Navigate to="/employee/dashboard" replace />} />
    </Routes>
  );

  // If on login page, render full-screen without sidebar or top navigation
  if (location.pathname === '/login' || location.pathname.startsWith('/login/')) {
    return routes;
  }

  return <AppLayout>{routes}</AppLayout>;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <MainPortalContent />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
