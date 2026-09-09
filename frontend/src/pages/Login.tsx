import React from 'react';
import { useAuth } from '../auth/AuthContext';
import { Sparkles, ShieldCheck, UserCheck, Lock } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, switchRole, isDevMode } = useAuth();

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        background: 'radial-gradient(ellipse at top, #1e293b 0%, #0a0d14 70%)',
      }}
    >
      <div
        className="card card-glass fade-in"
        style={{
          maxWidth: '480px',
          width: '100%',
          padding: 'clamp(24px, 5vw, 40px) clamp(16px, 4vw, 32px)',
          textAlign: 'center',
          boxShadow: 'var(--shadow-lg)',
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '14px',
            background: 'var(--gradient-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px auto',
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)',
          }}
        >
          <Sparkles size={30} color="#fff" />
        </div>

        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginBottom: '8px' }}>
          Tangentia Portal
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '28px', lineHeight: 1.5 }}>
          Internal Employee Referral & Talent Acquisition System. Authenticate with your company Microsoft account to submit and manage referrals.
        </p>

        {/* Live Microsoft SSO button */}
        <button
          className="btn btn-primary"
          style={{
            width: '100%',
            padding: '13px 20px',
            fontSize: '0.95rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}
          onClick={login}
        >
          <svg width="20" height="20" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 0H0V10H10V0Z" fill="#F25022"/>
            <path d="M21 0H11V10H21V0Z" fill="#7FBA00"/>
            <path d="M10 11H0V21H10V11Z" fill="#00A4EF"/>
            <path d="M21 11H11V21H21V11Z" fill="#FFB900"/>
          </svg>
          Sign in with Microsoft Entra ID
        </button>

        {/* Development Quick Role Switcher */}
        {isDevMode && (
          <div
            style={{
              marginTop: '24px',
              padding: '16px',
              background: 'rgba(15, 19, 29, 0.7)',
              borderRadius: '10px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: '#60a5fa',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                marginBottom: '12px',
              }}
            >
              Development Quick Access
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn btn-secondary btn-sm"
                style={{ flex: 1 }}
                onClick={async () => {
                  await switchRole('employee');
                }}
              >
                <UserCheck size={14} /> As Employee
              </button>

              <button
                className="btn btn-secondary btn-sm"
                style={{ flex: 1 }}
                onClick={async () => {
                  await switchRole('hr_admin');
                }}
              >
                <ShieldCheck size={14} /> As HR Admin
              </button>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: '24px' }}>
          <Lock size={12} /> Protected by Microsoft Entra ID & SharePoint Cloud
        </div>
      </div>
    </div>
  );
};
