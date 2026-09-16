import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
  Sparkles,
  ShieldCheck,
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  UserCheck,
  FileSpreadsheet,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, isHR, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If already logged in as HR, redirect to HR Dashboard
  useEffect(() => {
    if (isHR) {
      navigate('/hr/dashboard', { replace: true });
    }
  }, [isHR, navigate]);

  const validateEmail = (val: string): boolean => {
    return val.trim().toLowerCase().endsWith('@tangentia.com');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim();
    if (!validateEmail(cleanEmail)) {
      setErrorMessage('Access restricted. Please use your official @tangentia.com HR email address.');
      return;
    }

    if (!password) {
      setErrorMessage('Please enter your HR portal password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(cleanEmail, password);
      // Redirect to the intended page or default to HR dashboard
      const from = (location.state as any)?.from?.pathname || '/hr/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed. Please verify your credentials configured in the Excel file.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
        background: 'radial-gradient(ellipse at top, #1e293b 0%, #0a0d14 70%)',
      }}
    >
      <div
        className="card card-glass fade-in"
        style={{
          maxWidth: '460px',
          width: '100%',
          padding: 'clamp(24px, 5vw, 40px) clamp(20px, 4vw, 32px)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          position: 'relative',
        }}
      >
        {/* Back to Portal link */}
        <div style={{ marginBottom: '16px' }}>
          <button
            type="button"
            onClick={() => navigate('/employee/dashboard')}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.82rem',
              cursor: 'pointer',
              padding: '4px 0',
              fontWeight: 500,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
          >
            <ArrowLeft size={15} /> Back to Referral Portal
          </button>
        </div>

        {/* Top Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto',
              boxShadow: '0 0 24px rgba(99, 102, 241, 0.45)',
            }}
          >
            <ShieldCheck size={30} color="#fff" />
          </div>

          <h2 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#fff', marginBottom: '6px' }}>
            Tangentia HR Portal
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
            Sign in to access candidate management, job positions, and referral analytics.
          </p>
        </div>

        {/* Notice that employees do not need to sign in */}
        <div
          style={{
            background: 'rgba(59, 130, 246, 0.08)',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            borderRadius: '10px',
            padding: '12px 14px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            fontSize: '0.84rem',
            color: '#bfdbfe',
            lineHeight: 1.45,
          }}
        >
          <UserCheck size={18} style={{ flexShrink: 0, marginTop: '2px', color: '#60a5fa' }} />
          <div>
            <strong>Are you an employee?</strong> Login is only required for HR administrators. You can browse jobs and submit referrals directly!
            <div style={{ marginTop: '6px' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => navigate('/employee/dashboard')}
                style={{
                  fontSize: '0.78rem',
                  padding: '4px 10px',
                  background: 'rgba(59, 130, 246, 0.2)',
                  borderColor: 'rgba(59, 130, 246, 0.4)',
                  color: '#93c5fd',
                }}
              >
                Go to Employee Portal <ArrowRight size={12} />
              </button>
            </div>
          </div>
        </div>

        {/* Error notification */}
        {errorMessage && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: '10px',
              padding: '12px 14px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              color: '#fca5a5',
              fontSize: '0.86rem',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px', color: '#ef4444' }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: '18px' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Mail size={14} color="#93c5fd" />
              HR Email Address (@tangentia.com)
            </label>
            <input
              type="email"
              required
              className="form-input"
              placeholder="e.g. hr.lead@tangentia.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errorMessage) setErrorMessage(null);
              }}
              style={{
                borderColor: email && !validateEmail(email) ? 'rgba(239, 68, 68, 0.5)' : undefined,
              }}
            />
            {email && !validateEmail(email) && (
              <span style={{ fontSize: '0.75rem', color: '#f87171', marginTop: '4px', display: 'block' }}>
                Must be an @tangentia.com domain email address
              </span>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: '22px' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Lock size={14} color="#93c5fd" />
              HR Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                className="form-input"
                placeholder="Enter password from Excel"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                style={{ paddingRight: '40px' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting || isAuthLoading}
            style={{
              width: '100%',
              padding: '13px 20px',
              fontSize: '0.96rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
            }}
          >
            {isSubmitting ? (
              'Authenticating...'
            ) : (
              <>
                <ShieldCheck size={18} /> Sign In to HR Portal
              </>
            )}
          </button>
        </form>

        {/* Excel storage info banner */}
        <div
          style={{
            marginTop: '24px',
            padding: '12px 14px',
            background: 'rgba(15, 23, 42, 0.65)',
            border: '1px dashed rgba(255, 255, 255, 0.12)',
            borderRadius: '10px',
            fontSize: '0.78rem',
            color: 'var(--text-muted)',
            lineHeight: 1.45,
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
          }}
        >
          <FileSpreadsheet size={16} color="#34d399" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong style={{ color: '#e2e8f0' }}>Excel Credential Storage:</strong> Passwords are maintained in the{' '}
            <code style={{ color: '#93c5fd', background: 'rgba(30, 41, 59, 0.8)', padding: '1px 5px', borderRadius: '4px' }}>
              Users
            </code>{' '}
            sheet of <code style={{ color: '#93c5fd', background: 'rgba(30, 41, 59, 0.8)', padding: '1px 5px', borderRadius: '4px' }}>Tangentia_Referrals.xlsx</code>.
            Default test account:{' '}
            <span style={{ color: '#a7f3d0' }}>hr.lead@tangentia.com</span> /{' '}
            <span style={{ color: '#a7f3d0' }}>TangentiaHR@2026</span>
          </div>
        </div>
      </div>
    </div>
  );
};
