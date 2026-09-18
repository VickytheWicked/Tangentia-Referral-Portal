import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  UserCheck,
  UserX,
  KeyRound,
  FileSpreadsheet,
} from 'lucide-react';

type AuthErrorType = 'user_not_found' | 'password_incorrect' | 'role_restricted' | 'domain_invalid' | 'general' | null;

export const LoginPage: React.FC = () => {
  const { login, isHR, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<AuthErrorType>(null);

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
    setErrorType(null);

    const cleanEmail = email.trim();
    if (!validateEmail(cleanEmail)) {
      setErrorType('domain_invalid');
      setErrorMessage('Access restricted. Please use your official @tangentia.com HR email address.');
      return;
    }

    if (!password) {
      setErrorType('password_incorrect');
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
      const rawMsg = err.message || '';
      const lower = rawMsg.toLowerCase();

      if (
        lower.includes('user does not exist') ||
        lower.includes('account not found') ||
        lower.includes('not registered') ||
        lower.includes('user not found')
      ) {
        setErrorType('user_not_found');
        setErrorMessage(
          'User does not exist. No HR account found for this email address. Please check your email or contact the administrator.'
        );
      } else if (
        (lower.includes('password') && (lower.includes('incorrect') || lower.includes('invalid'))) ||
        lower.includes('credentials')
      ) {
        setErrorType('password_incorrect');
        setErrorMessage(
          'Password incorrect. The password you entered does not match our records. Please verify and try again.'
        );
      } else if (
        lower.includes('access restricted') ||
        lower.includes('employee') ||
        lower.includes('forbidden') ||
        lower.includes('403')
      ) {
        setErrorType('role_restricted');
        setErrorMessage(
          'Access restricted to HR administrators only. Employee accounts do not have access to this portal and do not require login.'
        );
      } else {
        setErrorType('general');
        setErrorMessage(rawMsg || 'Login failed. Please verify your credentials configured in the Excel file.');
      }
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

        {/* User Does Not Exist Warning Banner */}
        {errorType === 'user_not_found' && (
          <div
            className="fade-in"
            style={{
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.16) 0%, rgba(185, 28, 28, 0.09) 100%)',
              border: '1px solid rgba(239, 68, 68, 0.45)',
              borderRadius: '12px',
              padding: '14px 16px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              boxShadow: '0 4px 16px rgba(239, 68, 68, 0.14)',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(239, 68, 68, 0.22)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                color: '#f87171',
              }}
            >
              <UserX size={18} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, color: '#fca5a5', fontSize: '0.92rem', marginBottom: '3px' }}>
                User Does Not Exist
              </div>
              <div style={{ color: '#fecaca', fontSize: '0.84rem', lineHeight: 1.45 }}>
                {errorMessage}
              </div>
            </div>
          </div>
        )}

        {/* Password Incorrect Warning Banner */}
        {errorType === 'password_incorrect' && (
          <div
            className="fade-in"
            style={{
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.18) 0%, rgba(220, 38, 38, 0.12) 100%)',
              border: '1px solid rgba(245, 158, 11, 0.5)',
              borderRadius: '12px',
              padding: '14px 16px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              boxShadow: '0 4px 16px rgba(245, 158, 11, 0.14)',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(245, 158, 11, 0.22)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                color: '#fbbf24',
              }}
            >
              <KeyRound size={18} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, color: '#fde68a', fontSize: '0.92rem', marginBottom: '3px' }}>
                Password Incorrect
              </div>
              <div style={{ color: '#fef3c7', fontSize: '0.84rem', lineHeight: 1.45 }}>
                {errorMessage}
              </div>
            </div>
          </div>
        )}

        {/* Role Restricted Banner */}
        {errorType === 'role_restricted' && (
          <div
            className="fade-in"
            style={{
              background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.16) 0%, rgba(59, 130, 246, 0.1) 100%)',
              border: '1px solid rgba(168, 85, 247, 0.45)',
              borderRadius: '12px',
              padding: '14px 16px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(168, 85, 247, 0.22)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                color: '#c084fc',
              }}
            >
              <ShieldAlert size={18} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, color: '#e9d5ff', fontSize: '0.92rem', marginBottom: '3px' }}>
                Access Restricted to HR Admins
              </div>
              <div style={{ color: '#f3e8ff', fontSize: '0.84rem', lineHeight: 1.45, marginBottom: '8px' }}>
                {errorMessage}
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => navigate('/employee/dashboard')}
                style={{
                  fontSize: '0.78rem',
                  padding: '4px 10px',
                  background: 'rgba(168, 85, 247, 0.25)',
                  borderColor: 'rgba(168, 85, 247, 0.5)',
                  color: '#e9d5ff',
                }}
              >
                Go to Employee Portal <ArrowRight size={12} />
              </button>
            </div>
          </div>
        )}

        {/* Generic or Domain Error notification */}
        {(errorType === 'domain_invalid' || errorType === 'general') && errorMessage && (
          <div
            className="fade-in"
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
                if (errorType === 'user_not_found' || errorType === 'domain_invalid') {
                  setErrorType(null);
                  setErrorMessage(null);
                }
              }}
              style={{
                borderColor:
                  errorType === 'user_not_found'
                    ? '#ef4444'
                    : email && !validateEmail(email)
                    ? 'rgba(239, 68, 68, 0.5)'
                    : undefined,
                boxShadow: errorType === 'user_not_found' ? '0 0 0 3px rgba(239, 68, 68, 0.2)' : undefined,
              }}
            />
            {errorType === 'user_not_found' && (
              <div
                className="fade-in"
                style={{
                  fontSize: '0.78rem',
                  color: '#f87171',
                  marginTop: '5px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  fontWeight: 500,
                }}
              >
                <UserX size={13} />
                <span>User does not exist in the system</span>
              </div>
            )}
            {email && !validateEmail(email) && errorType !== 'user_not_found' && (
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
                  if (errorType === 'password_incorrect') {
                    setErrorType(null);
                    setErrorMessage(null);
                  }
                }}
                style={{
                  paddingRight: '40px',
                  borderColor: errorType === 'password_incorrect' ? '#f59e0b' : undefined,
                  boxShadow: errorType === 'password_incorrect' ? '0 0 0 3px rgba(245, 158, 11, 0.25)' : undefined,
                }}
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
            {errorType === 'password_incorrect' && (
              <div
                className="fade-in"
                style={{
                  fontSize: '0.78rem',
                  color: '#fbbf24',
                  marginTop: '5px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  fontWeight: 500,
                }}
              >
                <KeyRound size={13} />
                <span>Password incorrect. Please check and try again.</span>
              </div>
            )}
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
