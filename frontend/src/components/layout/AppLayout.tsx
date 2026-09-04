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
  Sparkles,
} from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { role, switchRole, isDevMode } = useAuth();
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
    if (path.includes('/employee/referrals') || path.includes('/employee/my-referrals')) return 'Candidate Referrals';
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
                className={`nav-item ${
                  location.pathname === '/employee/referrals' || location.pathname === '/employee/my-referrals'
                    ? 'active'
                    : ''
                }`}
                onClick={() => navigate('/employee/referrals')}
              >
                <Users size={18} />
                <span>Referrals</span>
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
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-navbar">
          <div className="navbar-left">
            <h2 className="page-title">{getPageTitle()}</h2>
          </div>
        </header>

        <main className="content-area">{children}</main>
      </div>
    </div>
  );
};
