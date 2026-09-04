import React from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
  Users,
  PlusCircle,
  FolderKanban,
  BarChart3,
  Briefcase,
  Layers,
  ShieldCheck,
  User as UserIcon,
  Sparkles,
} from 'lucide-react';

interface AppLayoutProps {
  currentTab: string;
  onNavigate: (tab: string) => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentTab,
  onNavigate,
  children,
}) => {
  const { user, role, switchRole, isDevMode } = useAuth();

  const isHR = role === 'hr_admin';

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-logo-container">
            <Sparkles size={20} color="#ffffff" />
          </div>
          <div>
            <h1 className="brand-name">Tangentia</h1>
            <span className="brand-tag">Referral Portal</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">
            {isHR ? 'HR Administration' : 'Employee Workspace'}
          </div>

          {!isHR ? (
            <>
              <div
                className={`nav-item ${currentTab === 'employee-dashboard' ? 'active' : ''}`}
                onClick={() => onNavigate('employee-dashboard')}
              >
                <Layers size={18} />
                <span>Dashboard</span>
              </div>

              <div
                className={`nav-item ${currentTab === 'submit-referral' ? 'active' : ''}`}
                onClick={() => onNavigate('submit-referral')}
              >
                <PlusCircle size={18} />
                <span>Submit Referral</span>
              </div>

              <div
                className={`nav-item ${currentTab === 'my-referrals' ? 'active' : ''}`}
                onClick={() => onNavigate('my-referrals')}
              >
                <Users size={18} />
                <span>My Referrals</span>
              </div>
            </>
          ) : (
            <>
              <div
                className={`nav-item ${currentTab === 'hr-dashboard' ? 'active' : ''}`}
                onClick={() => onNavigate('hr-dashboard')}
              >
                <Layers size={18} />
                <span>HR Dashboard</span>
              </div>

              <div
                className={`nav-item ${currentTab === 'all-referrals' ? 'active' : ''}`}
                onClick={() => onNavigate('all-referrals')}
              >
                <FolderKanban size={18} />
                <span>All Referrals</span>
              </div>

              <div
                className={`nav-item ${currentTab === 'job-positions' ? 'active' : ''}`}
                onClick={() => onNavigate('job-positions')}
              >
                <Briefcase size={18} />
                <span>Job Openings</span>
              </div>

              <div
                className={`nav-item ${currentTab === 'analytics' ? 'active' : ''}`}
                onClick={() => onNavigate('analytics')}
              >
                <BarChart3 size={18} />
                <span>Analytics</span>
              </div>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: isHR ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' : 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 700,
                fontSize: '0.85rem',
              }}
            >
              {user?.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user?.name || 'Loading user...'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user?.email || 'authenticated'}
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-navbar">
          <div className="navbar-left">
            <h2 className="page-title">
              {currentTab === 'employee-dashboard' && 'Employee Dashboard'}
              {currentTab === 'submit-referral' && 'Submit New Referral'}
              {currentTab === 'my-referrals' && 'My Submitted Referrals'}
              {currentTab === 'hr-dashboard' && 'HR Referral Overview'}
              {currentTab === 'all-referrals' && 'Enterprise Candidate Database'}
              {currentTab === 'job-positions' && 'Job Openings Management'}
              {currentTab === 'analytics' && 'Referral Funnel & Analytics'}
            </h2>
          </div>

          <div className="navbar-right">
            {/* Dev Mode Role Switcher Toggle */}
            {isDevMode && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: 'rgba(20, 25, 38, 0.9)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  padding: '4px',
                  gap: '4px',
                }}
              >
                <button
                  className={`btn btn-sm ${!isHR ? 'btn-primary' : 'btn-outline'}`}
                  style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                  onClick={() => {
                    switchRole('employee');
                    onNavigate('employee-dashboard');
                  }}
                >
                  <UserIcon size={12} />
                  Employee View
                </button>
                <button
                  className={`btn btn-sm ${isHR ? 'btn-primary' : 'btn-outline'}`}
                  style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                  onClick={() => {
                    switchRole('hr_admin');
                    onNavigate('hr-dashboard');
                  }}
                >
                  <ShieldCheck size={12} />
                  HR Admin View
                </button>
              </div>
            )}

            {/* Current Role Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '8px',
                background: isHR ? 'rgba(139, 92, 246, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                border: `1px solid ${isHR ? 'rgba(139, 92, 246, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
                color: isHR ? '#c084fc' : '#60a5fa',
                fontSize: '0.78rem',
                fontWeight: 600,
              }}
            >
              {isHR ? <ShieldCheck size={14} /> : <UserIcon size={14} />}
              <span>{isHR ? 'HR Administrator' : 'Company Employee'}</span>
            </div>
          </div>
        </header>

        <main className="content-area">
          {children}
        </main>
      </div>
    </div>
  );
};
