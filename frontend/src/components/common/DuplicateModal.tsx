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
}

export const DuplicateModal: React.FC<DuplicateModalProps> = ({
  isOpen,
  onClose,
  matches,
  onConfirmSubmit,
  candidateName,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Possible Duplicate Candidate Found"
      maxWidth="650px"
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Review & Edit
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
            border: '1px solid rgba(245, 158, 11, 0.3)',
            padding: '16px',
            borderRadius: '10px',
          }}
        >
          <AlertTriangle color="#f59e0b" size={24} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ color: '#fbbf24', fontSize: '0.95rem', fontWeight: 600, marginBottom: '4px' }}>
              Potential Existing Referral Detected
            </h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', lineHeight: 1.5 }}>
              One or more candidates in the system match details for <strong>{candidateName}</strong>. Please review below to avoid duplicate candidate submissions.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
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
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                  {m.candidate_name}
                </span>
                <StatusBadge status={m.status} />
              </div>

              <div className="responsive-info-grid" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', gap: '6px' }}>
                <div><strong>Position:</strong> {m.position_title}</div>
                <div><strong>Referral ID:</strong> <span style={{ fontFamily: 'var(--font-mono)' }}>{m.referral_number}</span></div>
                <div><strong>Referred by:</strong> {m.referred_by_name}</div>
                <div><strong>Submitted:</strong> {m.created_at}</div>
              </div>

              <div style={{ fontSize: '0.78rem', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.08)', padding: '6px 10px', borderRadius: '6px' }}>
                <strong>Reason:</strong> {m.match_reason}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  );
};
