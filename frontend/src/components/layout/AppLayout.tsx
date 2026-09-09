import React, { useEffect, useState } from 'react';
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
  Menu,
  X,
  ShieldCheck,
  UserCheck,
  ArrowLeftRight,
} from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { user, role, switchRole, isDevMode } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

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

  // Close mobile menu whenever the route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

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

  const handleNavClick = (path: string) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  const handleToggleRole = async () => {
    const nextRole = role === 'hr_admin' ? 'employee' : 'hr_admin';
    await switchRole(nextRole);
    if (nextRole === 'hr_admin') {
      navigate('/hr/dashboard');
    } else {
      navigate('/employee/dashboard');
    }
  };

  return (
    <div className="app-container">
      {/* Backdrop for mobile drawer */}
      {mobileMenuOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Navigation (Desktop Fixed & Mobile Drawer) */}
      <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="sidebar-header" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="brand-logo-container">
              <Sparkles size={20} color="#ffffff" />
            </div>
            <div>
              <h1 className="brand-name">Tangentia</h1>
              <span className="brand-tag">{isHR ? 'Talent Acquisition' : 'Referral Portal'}</span>
            </div>
          </div>
          {/* Close button inside mobile drawer */}
          <button
            className="mobile-menu-btn"
            style={{ width: '32px', height: '32px' }}
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">
            {isHR ? 'HR Administration' : 'Employee Workspace'}
          </div>

          {!isHR ? (
            <>
              <div
                className={`nav-item ${location.pathname === '/employee' || location.pathname === '/employee/dashboard'
                    ? 'active'
                    : ''
                  }`}
                onClick={() => handleNavClick('/employee/dashboard')}
              >
                <Layers size={18} />
                <span>Dashboard</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/employee/submit' ? 'active' : ''}`}
                onClick={() => handleNavClick('/employee/submit')}
              >
                <PlusCircle size={18} />
                <span>Submit Referral</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/employee/referrals' || location.pathname === '/employee/my-referrals'
                    ? 'active'
                    : ''
                  }`}
                onClick={() => handleNavClick('/employee/referrals')}
              >
                <Users size={18} />
                <span>Referrals</span>
              </div>
            </>
          ) : (
            <>
              <div
                className={`nav-item ${location.pathname === '/hr' || location.pathname === '/hr/dashboard'
                    ? 'active'
                    : ''
                  }`}
                onClick={() => handleNavClick('/hr/dashboard')}
              >
                <Layers size={18} />
                <span>HR Dashboard</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/referrals' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/referrals')}
              >
                <FolderKanban size={18} />
                <span>All Referrals</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/jobs' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/jobs')}
              >
                <Briefcase size={18} />
                <span>Job Openings</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/analytics' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/analytics')}
              >
                <BarChart3 size={18} />
                <span>Analytics</span>
              </div>
            </>
          )}

          {/* Quick Role Switcher in Sidebar Footer for Mobile/Desktop */}
          {isDevMode && (
            <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
              <div className="nav-section-title" style={{ padding: '0 0 8px 0' }}>
                Environment Mode
              </div>
              <button
                className="btn btn-secondary btn-sm"
                style={{ width: '100%', justifyContent: 'center', fontSize: '0.8rem' }}
                onClick={handleToggleRole}
              >
                <ArrowLeftRight size={14} />
                Switch to {role === 'hr_admin' ? 'Employee' : 'HR Admin'}
              </button>
            </div>
          )}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-navbar">
          <div className="navbar-left">
            <button
              className="mobile-menu-btn"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <h2 className="page-title">{getPageTitle()}</h2>
          </div>

          <div className="navbar-right">
            {/* User Profile / Role Pill */}
            {/* <div className="header-user-pill" title={user?.email || 'Logged in user'}>
              <div className="header-user-avatar">
                {role === 'hr_admin' ? <ShieldCheck size={16} /> : <UserCheck size={16} />}
              </div>
              <span className="header-user-name">
                {user?.name || (role === 'hr_admin' ? 'HR Lead' : 'Employee')}
              </span>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  padding: '2px 7px',
                  borderRadius: '10px',
                  background: role === 'hr_admin' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                  color: role === 'hr_admin' ? '#c4b5fd' : '#93c5fd',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                {role === 'hr_admin' ? 'HR' : 'Emp'}
              </span>
            </div> */}
          </div>
        </header>

        <main className="content-area">{children}</main>

        {/* Mobile Bottom Navigation Bar for instantaneous navigation on phones */}
        <nav className="mobile-bottom-nav">
          {!isHR ? (
            <>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/employee' || location.pathname === '/employee/dashboard'
                    ? 'active'
                    : ''
                  }`}
                onClick={() => handleNavClick('/employee/dashboard')}
              >
                <Layers size={18} />
                <span>Dashboard</span>
              </div>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/employee/submit' ? 'active' : ''
                  }`}
                onClick={() => handleNavClick('/employee/submit')}
              >
                <PlusCircle size={18} />
                <span>Submit</span>
              </div>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/employee/referrals' || location.pathname === '/employee/my-referrals'
                    ? 'active'
                    : ''
                  }`}
                onClick={() => handleNavClick('/employee/referrals')}
              >
                <Users size={18} />
                <span>Referrals</span>
              </div>
            </>
          ) : (
            <>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/hr' || location.pathname === '/hr/dashboard'
                    ? 'active'
                    : ''
                  }`}
                onClick={() => handleNavClick('/hr/dashboard')}
              >
                <Layers size={18} />
                <span>Dashboard</span>
              </div>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/hr/referrals' ? 'active' : ''
                  }`}
                onClick={() => handleNavClick('/hr/referrals')}
              >
                <FolderKanban size={18} />
                <span>Candidates</span>
              </div>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/hr/jobs' ? 'active' : ''
                  }`}
                onClick={() => handleNavClick('/hr/jobs')}
              >
                <Briefcase size={18} />
                <span>Openings</span>
              </div>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/hr/analytics' ? 'active' : ''
                  }`}
                onClick={() => handleNavClick('/hr/analytics')}
              >
                <BarChart3 size={18} />
                <span>Analytics</span>
              </div>
            </>
          )}
        </nav>
      </div>
    </div>
  );
};
