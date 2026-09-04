import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { EmployeeDashboard } from './pages/employee/EmployeeDashboard';
import { SubmitReferralPage } from './pages/employee/SubmitReferralPage';
import { MyReferralsPage } from './pages/employee/MyReferralsPage';
import { HRDashboard } from './pages/hr/HRDashboard';
import { AllReferralsPage } from './pages/hr/AllReferralsPage';
import { JobPositionsPage } from './pages/hr/JobPositionsPage';
import { AnalyticsPage } from './pages/hr/AnalyticsPage';

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

  return (
    <AppLayout>
      <Routes>
        {/* Default Landing -> Redirects to Employee Dashboard */}
        <Route path="/" element={<Navigate to="/employee/dashboard" replace />} />

        {/* ================================================================ */}
        {/* Employee Workspace Routes                                         */}
        {/* ================================================================ */}
        <Route path="/employee" element={<Navigate to="/employee/dashboard" replace />} />
        <Route
          path="/employee/dashboard"
          element={
            <EmployeeDashboard
              onNavigate={(tab) => {
                if (tab === 'submit-referral') navigate('/employee/submit');
                else if (tab === 'my-referrals' || tab === 'referrals') navigate('/employee/referrals');
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
        {/* HR Administration Hub Routes                                      */}
        {/* ================================================================ */}
        <Route path="/hr" element={<Navigate to="/hr/dashboard" replace />} />
        <Route
          path="/hr/dashboard"
          element={
            <HRDashboard
              onNavigate={(tab) => {
                if (tab === 'all-referrals') navigate('/hr/referrals');
                else if (tab === 'job-positions') navigate('/hr/jobs');
                else if (tab === 'analytics') navigate('/hr/analytics');
              }}
              onOpenCandidate={handleOpenCandidate}
            />
          }
        />
        <Route
          path="/hr/referrals"
          element={
            <AllReferralsPage
              initialSelectedId={selectedCandidateId}
              onClearInitialId={() => setSelectedCandidateId(null)}
            />
          }
        />
        <Route path="/hr/jobs" element={<JobPositionsPage />} />
        <Route path="/hr/analytics" element={<AnalyticsPage />} />

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/employee/dashboard" replace />} />
      </Routes>
    </AppLayout>
  );
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
