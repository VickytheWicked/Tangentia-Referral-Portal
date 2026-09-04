import React, { useState, useEffect } from 'react';
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
  const { user, role, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>(role === 'hr_admin' ? 'hr-dashboard' : 'employee-dashboard');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  // Sync default tab when role switches
  useEffect(() => {
    if (role === 'hr_admin') {
      setCurrentTab('hr-dashboard');
    } else {
      setCurrentTab('employee-dashboard');
    }
  }, [role]);

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
    setCurrentTab('all-referrals');
  };

  return (
    <AppLayout currentTab={currentTab} onNavigate={setCurrentTab}>
      {/* Employee Navigation */}
      {role === 'employee' && (
        <>
          {currentTab === 'employee-dashboard' && (
            <EmployeeDashboard onNavigate={setCurrentTab} />
          )}
          {currentTab === 'submit-referral' && (
            <SubmitReferralPage onReferralCreated={() => setCurrentTab('my-referrals')} />
          )}
          {currentTab === 'my-referrals' && (
            <MyReferralsPage onNavigate={setCurrentTab} />
          )}
        </>
      )}

      {/* HR Admin Navigation */}
      {role === 'hr_admin' && (
        <>
          {currentTab === 'hr-dashboard' && (
            <HRDashboard
              onNavigate={setCurrentTab}
              onOpenCandidate={handleOpenCandidate}
            />
          )}
          {currentTab === 'all-referrals' && (
            <AllReferralsPage
              initialSelectedId={selectedCandidateId}
              onClearInitialId={() => setSelectedCandidateId(null)}
            />
          )}
          {currentTab === 'job-positions' && <JobPositionsPage />}
          {currentTab === 'analytics' && <AnalyticsPage />}
        </>
      )}
    </AppLayout>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainPortalContent />
    </AuthProvider>
  );
};

export default App;
