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
  Award,
  Menu,
  X,
  ShieldCheck,
  LogOut,
  LogIn,
} from 'lucide-react';
import {
  resolveReleaseSignature,
  resolveBuildPrefix,
  resolveBuildAuthor,
  registerSignatureTriggers,
} from '../../utils/systemMeta';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { user, isHR, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [showMadeBy, setShowMadeBy] = useState<boolean>(false);

  useEffect(() => {
    const unregister = registerSignatureTriggers(() => {
      setShowMadeBy((prev) => !prev);
    });
    return unregister;
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('/hired-history')) return 'Hired Referral History';
    if (path.includes('/employee/submit')) return 'Submit New Referral';
    if (path.includes('/employee/referrals') || path.includes('/employee/my-referrals')) return 'Candidate Referrals';
    if (path.startsWith('/employee/openings')) return 'Available Openings';
    if (path.startsWith('/employee')) return 'Employee Dashboard';
    if (path.includes('/hr/referrals')) return 'Enterprise Candidate Database';
    if (path.includes('/hr/suggestions')) return 'Candidate AI Suggestions';
    if (path.includes('/hr/jobs')) return 'Job Openings Management';
    if (path.includes('/hr/analytics')) return 'Referral Funnel & Analytics';
    if (path.startsWith('/hr')) return 'HR Referral Overview';
    if (path.includes('/login')) return 'HR Portal Login';
    return 'Tangentia Referral Portal';
  };

  const handleNavClick = (path: string) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/employee/dashboard');
  };

  // Do not render sidebar/navbar layout on login page
  if (location.pathname === '/login' || location.pathname.startsWith('/login/')) {
    return <>{children}</>;
  }

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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div className="brand-logo-badge" title="Tangentia">
              <img
                src="/Tangentia-Logo-2026-Black-scaled.png"
                alt="Tangentia"
                className="brand-logo-img"
              />
            </div>
            <span className="brand-tag" style={{ paddingLeft: '2px' }}>
              {isHR ? 'HR Administration' : 'Referral Portal'}
            </span>
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
                className={`nav-item ${location.pathname === '/employee/openings' ? 'active' : ''}`}
                onClick={() => handleNavClick('/employee/openings')}
              >
                <Briefcase size={18} />
                <span>Available Openings</span>
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
                <span>Candidate Referrals</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/employee/hired-history' ? 'active' : ''}`}
                onClick={() => handleNavClick('/employee/hired-history')}
              >
                <Award size={18} />
                <span>Hired History</span>
              </div>
            </>
          ) : (
            <>
              <div
                className={`nav-item ${location.pathname === '/hr' || location.pathname === '/hr/dashboard' ? 'active' : ''
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
                <span>All Candidates</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/suggestions' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/suggestions')}
              >
                <Sparkles size={18} />
                <span>HR Suggestions</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/jobs' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/jobs')}
              >
                <Briefcase size={18} />
                <span>Manage Openings</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/analytics' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/analytics')}
              >
                <BarChart3 size={18} />
                <span>Analytics</span>
              </div>

              <div
                className={`nav-item ${location.pathname === '/hr/hired-history' ? 'active' : ''}`}
                onClick={() => handleNavClick('/hr/hired-history')}
              >
                <Award size={18} />
                <span>Hired History</span>
              </div>
            </>
          )}

          {/* Sidebar Footer Action */}
          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            {isHR ? (
              <button
                className="btn btn-secondary btn-sm"
                style={{ width: '100%', justifyContent: 'center', fontSize: '0.82rem', gap: '8px' }}
                onClick={handleLogout}
              >
                <LogOut size={15} />
                Sign Out (HR)
              </button>
            ) : (
              <button
                className="btn btn-secondary btn-sm"
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  fontSize: '0.82rem',
                  gap: '8px',
                  borderColor: 'rgba(59, 130, 246, 0.4)',
                  color: '#93c5fd',
                }}
                onClick={() => handleNavClick('/login')}
              >
                <ShieldCheck size={15} color="#60a5fa" />
                HR Admin Sign In
              </button>
            )}

            {showMadeBy && (
              <div
                style={{
                  marginTop: '12px',
                  textAlign: 'center',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  letterSpacing: '0.02em',
                  userSelect: 'none',
                }}
              >
                <span>{resolveBuildPrefix()}</span>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{resolveBuildAuthor()}</span>
              </div>
            )}
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-navbar">
          <div className="navbar-left" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="mobile-menu-btn"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <div className="brand-logo-badge-sm visible-mobile-flex" title="Tangentia">
              <img
                src="/Tangentia-Logo-2026-Black-scaled.png"
                alt="Tangentia"
                className="brand-logo-img"
              />
            </div>
            <h2 className="page-title">{getPageTitle()}</h2>
          </div>

          <div className="navbar-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {isHR ? (
              <>
                <div
                  className="header-user-pill"
                  title={user?.email || 'Logged in as HR Admin'}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <div className="header-user-avatar" style={{ background: 'rgba(139, 92, 246, 0.25)', color: '#c4b5fd' }}>
                    <ShieldCheck size={16} />
                  </div>
                  <span className="header-user-name">
                    {user?.name || 'HR Administrator'}
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '2px 7px',
                      borderRadius: '10px',
                      background: 'rgba(139, 92, 246, 0.25)',
                      color: '#c4b5fd',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    HR
                  </span>
                </div>

                {/* <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleLogout}
                  style={{
                    fontSize: '0.8rem',
                    padding: '6px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                  title="Sign out of HR Admin"
                >
                  <LogOut size={14} />
                  <span className="hidden-mobile">Sign Out</span>
                </button> */}
              </>
            ) : (
              // <button
              //   className="btn btn-secondary btn-sm"
              //   onClick={() => navigate('/login')}
              //   style={{
              //     fontSize: '0.82rem',
              //     padding: '6px 14px',
              //     display: 'flex',
              //     alignItems: 'center',
              //     gap: '6px',
              //     borderColor: 'rgba(59, 130, 246, 0.35)',
              //     background: 'rgba(59, 130, 246, 0.12)',
              //     color: '#93c5fd',
              //   }}
              // >
              //   <ShieldCheck size={15} color="#60a5fa" />
              //   <span>HR Login</span>
              // </button>

              // <div>
              //   {/* <div className="header-user-avatar" style={{ background: 'rgba(139, 92, 246, 0.25)', color: '#c4b5fd' }}>
              //     <ShieldCheck size={16} />
              //   </div> */}
              //   <span
              //     style={{
              //       fontSize: '0.68rem',
              //       fontWeight: 700,
              //       padding: '2px 7px',
              //       borderRadius: '10px',
              //       background: 'rgba(139, 92, 246, 0.25)',
              //       color: '#c4b5fd',
              //       textTransform: 'uppercase',
              //       letterSpacing: '0.04em',
              //     }}
              //   >
              //     Employee
              //   </span>
              // </div>

              <div
                id="header-employee-pill"
                data-role="employee-badge"
                className="header-user-pill"
                title={showMadeBy ? resolveReleaseSignature() : 'Employee Dashboard (Click to reveal)'}
                onClick={() => setShowMadeBy((prev) => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'all 0.2s ease',
                  borderColor: showMadeBy ? 'rgba(56, 189, 248, 0.4)' : undefined,
                  background: showMadeBy ? 'rgba(15, 23, 42, 0.9)' : undefined,
                }}
              >
                <div
                  className="header-user-avatar"
                  style={{
                    background: showMadeBy ? 'rgba(56, 189, 248, 0.2)' : 'rgba(139, 92, 246, 0.25)',
                    color: showMadeBy ? '#38bdf8' : '#c4b5fd',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {showMadeBy ? <Sparkles size={16} /> : <ShieldCheck size={16} />}
                </div>
                <span
                  className="header-user-name"
                  style={{
                    maxWidth: 'none',
                    color: showMadeBy ? '#38bdf8' : 'var(--text-primary)',
                    fontWeight: showMadeBy ? 700 : 600,
                  }}
                >
                  {showMadeBy ? resolveReleaseSignature() : 'Employee'}
                </span>
              </div>
            )}
          </div>
        </header>

        <main className="content-area">{children}</main>

        {/* Mobile Bottom Navigation Bar */}
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
                className={`mobile-bottom-nav-item ${location.pathname === '/employee/openings' ? 'active' : ''
                  }`}
                onClick={() => handleNavClick('/employee/openings')}
              >
                <Briefcase size={18} />
                <span>Openings</span>
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
                className={`mobile-bottom-nav-item ${location.pathname === '/hr' || location.pathname === '/hr/dashboard' ? 'active' : ''
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
                className={`mobile-bottom-nav-item ${location.pathname === '/hr/suggestions' ? 'active' : ''
                  }`}
                onClick={() => handleNavClick('/hr/suggestions')}
              >
                <Sparkles size={18} />
                <span>Suggestions</span>
              </div>
              <div
                className={`mobile-bottom-nav-item ${location.pathname === '/hr/jobs' ? 'active' : ''}`}
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
