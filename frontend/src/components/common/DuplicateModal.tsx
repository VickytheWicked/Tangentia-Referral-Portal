import React from 'react';
import { Modal } from './Modal';
import { DuplicateMatch } from '../../types';
import { AlertTriangle, UserCheck, ArrowRight } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

interface DuplicateModalProps {
  isOpen: boolean;
  onClose: () => void;
  matches: DuplicateMatch[];
  onConfirmSubmit: () => void;
  candidateName: string;
  checkedEmail?: string;
  checkedPhone?: string;
}

export const DuplicateModal: React.FC<DuplicateModalProps> = ({
  isOpen,
  onClose,
  matches,
  onConfirmSubmit,
  candidateName,
  checkedEmail,
  checkedPhone,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Duplicate Candidate Detected"
      maxWidth="680px"
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Review & Edit Details
          </button>
          <button
            className="btn btn-primary"
            onClick={() => {
              onClose();
              onConfirmSubmit();
            }}
          >
            Confirm & Proceed with Submission
          </button>
        </>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '14px',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            padding: '16px',
            borderRadius: '10px',
          }}
        >
          <AlertTriangle color="#f59e0b" size={24} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ color: '#fbbf24', fontSize: '0.96rem', fontWeight: 700, marginBottom: '6px' }}>
              Potential Existing Referral Detected ({matches.length} match{matches.length > 1 ? 'es' : ''})
            </h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', lineHeight: 1.5, marginBottom: '10px' }}>
              The system detected that the trimmed details you entered match existing candidate records in the database. Please review the exact duplicate fields below:
            </p>
            <div
              style={{
                fontSize: '0.8rem',
                background: 'rgba(15, 23, 42, 0.65)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '8px 12px',
                borderRadius: '8px',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Trimmed Name: </span>
                <code style={{ color: '#93c5fd', fontWeight: 600 }}>"{candidateName.trim()}"</code>
              </div>
              {checkedEmail && (
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Trimmed Email: </span>
                  <code style={{ color: '#93c5fd', fontWeight: 600 }}>"{checkedEmail.trim()}"</code>
                </div>
              )}
              {checkedPhone && (
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Trimmed Phone: </span>
                  <code style={{ color: '#93c5fd', fontWeight: 600 }}>"{checkedPhone.trim()}"</code>
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {matches.map((m) => (
            <div
              key={m.referral_id}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.94rem' }}>
                  {m.candidate_name}
                </span>
                <StatusBadge status={m.status} />
              </div>

              <div className="responsive-info-grid" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', gap: '6px' }}>
                <div><strong>Position:</strong> {m.position_title}</div>
                <div><strong>Referral ID:</strong> <span style={{ fontFamily: 'var(--font-mono)', color: '#93c5fd' }}>{m.referral_number}</span></div>
                <div><strong>Existing Email:</strong> {m.candidate_email}</div>
                <div><strong>Referred by:</strong> {m.referred_by_name}</div>
                <div><strong>Date Submitted:</strong> {m.created_at}</div>
              </div>

              <div
                style={{
                  fontSize: '0.82rem',
                  color: '#fbbf24',
                  background: 'rgba(245, 158, 11, 0.1)',
                  borderLeft: '3px solid #f59e0b',
                  padding: '8px 12px',
                  borderRadius: '0 6px 6px 0',
                  lineHeight: 1.45,
                }}
              >
                <strong>Exact Duplicate Reason:</strong> {m.match_reason}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  );
};
