import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
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
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { user, role, switchRole, isDevMode } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isHR = location.pathname.startsWith('/hr');

  // Automatically sync dev role if DEV_MODE is enabled when route changes
  useEffect(() => {
    if (isDevMode) {
      if (isHR && role !== 'hr_admin') {
        switchRole('hr_admin');
      } else if (!isHR && role !== 'employee') {
        switchRole('employee');
      }
    }
  }, [isHR, isDevMode, role, switchRole]);

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('/employee/submit')) return 'Submit New Referral';
    if (path.includes('/employee/my-referrals')) return 'My Submitted Referrals';
    if (path.startsWith('/employee')) return 'Employee Dashboard';
    if (path.includes('/hr/referrals')) return 'Enterprise Candidate Database';
    if (path.includes('/hr/jobs')) return 'Job Openings Management';
    if (path.includes('/hr/analytics')) return 'Referral Funnel & Analytics';
    if (path.startsWith('/hr')) return 'HR Referral Overview';
    return 'Tangentia Referral Portal';
  };

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
            <span className="brand-tag">{isHR ? 'Talent Acquisition' : 'Referral Portal'}</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">
            {isHR ? 'HR Administration' : 'Employee Workspace'}
          </div>

          {!isHR ? (
            <>
              <div
                className={`nav-item ${
                  location.pathname === '/employee' || location.pathname === '/employee/dashboard'
                    ? 'active'
                    : ''
                }`}
                onClick={() => navigate('/employee/dashboard')}
              >
                <Layers size={18} />
                <span>Dashboard</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/employee/submit' ? 'active' : ''}`}
                onClick={() => navigate('/employee/submit')}
              >
                <PlusCircle size={18} />
                <span>Submit Referral</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/employee/my-referrals' ? 'active' : ''}`}
                onClick={() => navigate('/employee/my-referrals')}
              >
                <Users size={18} />
                <span>My Referrals</span>
              </div>
            </>
          ) : (
            <>
              <div
                className={`nav-item ${
                  location.pathname === '/hr' || location.pathname === '/hr/dashboard'
                    ? 'active'
                    : ''
                }`}
                onClick={() => navigate('/hr/dashboard')}
              >
                <Layers size={18} />
                <span>HR Dashboard</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/referrals' ? 'active' : ''}`}
                onClick={() => navigate('/hr/referrals')}
              >
                <FolderKanban size={18} />
                <span>All Referrals</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/jobs' ? 'active' : ''}`}
                onClick={() => navigate('/hr/jobs')}
              >
                <Briefcase size={18} />
                <span>Job Openings</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/analytics' ? 'active' : ''}`}
                onClick={() => navigate('/hr/analytics')}
              >
                <BarChart3 size={18} />
                <span>Analytics</span>
              </div>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: isHR
                  ? 'linear-gradient(135deg, #8b5cf6, #ec4899)'
                  : 'linear-gradient(135deg, #3b82f6, #06b6d4)',
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
              <div
                style={{
                  fontSize: '0.84rem',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                }}
              >
                {user?.name || 'Loading user...'}
              </div>
              <div
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                }}
              >
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
            <h2 className="page-title">{getPageTitle()}</h2>
          </div>

          <div className="navbar-right">
            {/* Active Site / Workspace Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                borderRadius: '8px',
                background: isHR ? 'rgba(139, 92, 246, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                border: `1px solid ${isHR ? 'rgba(139, 92, 246, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
                color: isHR ? '#c084fc' : '#60a5fa',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              {isHR ? <ShieldCheck size={15} /> : <UserIcon size={15} />}
              <span>{isHR ? 'HR Administration Hub' : 'Employee Workspace'}</span>
            </div>
          </div>
        </header>

        <main className="content-area">{children}</main>
      </div>
    </div>
  );
};
