import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowRight, Briefcase } from 'lucide-react';
import { Modal } from './Modal';

interface JobUnavailableModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobTitle?: string;
  onExploreOtherJobs?: () => void;
}

export const JobUnavailableModal: React.FC<JobUnavailableModalProps> = ({
  isOpen,
  onClose,
  jobTitle,
  onExploreOtherJobs,
}) => {
  const navigate = useNavigate();

  const handleExplore = () => {
    onClose();
    if (onExploreOtherJobs) {
      onExploreOtherJobs();
    } else {
      navigate('/employee/openings');
    }
  };

  const footer = (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px', width: '100%' }}>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        onClick={onClose}
      >
        Close
      </button>
      <button
        type="button"
        className="btn btn-primary btn-sm"
        onClick={handleExplore}
        style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
      >
        <Briefcase size={14} /> Browse Available Openings <ArrowRight size={14} />
      </button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Position No Longer Available"
      maxWidth="540px"
      footer={footer}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '12px 6px 16px' }}>
        {/* Warning Icon Badge */}
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '18px',
            boxShadow: '0 0 24px rgba(245, 158, 11, 0.18)',
          }}
        >
          <AlertTriangle size={32} color="#f59e0b" />
        </div>

        <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          {jobTitle ? `"${jobTitle}" is Closed` : 'Job Opening Unavailable'}
        </h4>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: '20px',
            background: 'rgba(239, 68, 68, 0.15)',
            color: '#f87171',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            fontSize: '0.78rem',
            fontWeight: 600,
            marginBottom: '16px',
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ef4444' }} />
          Deactivated / No Longer Open
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.6, marginBottom: '14px' }}>
          This job position has been filled, closed, or deactivated in the Tangentia CATS One ATS or by HR and is no longer accepting new candidate referrals.
        </p>

        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '0.82rem',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
            width: '100%',
            textAlign: 'left',
          }}
        >
          💡 <strong>Notice:</strong> Because this page was loaded earlier without refreshing, this opening was still visible on your screen. Active requisitions are refreshed live across the portal.
        </div>
      </div>
    </Modal>
  );
};
