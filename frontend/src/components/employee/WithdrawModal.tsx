import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../services/api';
import { AlertTriangle, RotateCcw, Loader2 } from 'lucide-react';

interface WithdrawModalProps {
  isOpen: boolean;
  onClose: () => void;
  referralId: string;
  candidateName: string;
  referralNumber?: string;
  onSuccess: () => void;
}

export const WithdrawModal: React.FC<WithdrawModalProps> = ({
  isOpen,
  onClose,
  referralId,
  candidateName,
  referralNumber,
  onSuccess,
}) => {
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await api.withdrawReferral(referralId, reason.trim() || undefined);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to withdraw referral.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Withdraw Candidate Referral"
      maxWidth="540px"
      footer={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px', width: '100%' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleSubmit}
            disabled={isSubmitting}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="spin" />
                <span>Withdrawing...</span>
              </>
            ) : (
              <>
                <RotateCcw size={16} />
                <span>Confirm Withdrawal</span>
              </>
            )}
          </button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {/* Warning Callout Box */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '14px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            padding: '16px',
            borderRadius: '12px',
          }}
        >
          <AlertTriangle color="#f87171" size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, color: '#f87171', fontSize: '0.95rem', marginBottom: '4px' }}>
              Are you sure you want to withdraw this referral?
            </div>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.45, margin: 0 }}>
              You are withdrawing the referral for <strong style={{ color: 'var(--text-primary)' }}>{candidateName}</strong>
              {referralNumber ? ` (${referralNumber})` : ''}. This will transition the application status to{' '}
              <span style={{ color: '#f87171', fontWeight: 600 }}>Withdrawn</span> and remove it from active review.
            </p>
          </div>
        </div>

        {error && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              fontSize: '0.85rem',
            }}
          >
            {error}
          </div>
        )}

        {/* Reason Input */}
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label" htmlFor="withdraw-reason">
            Reason for withdrawal (Optional)
          </label>
          <textarea
            id="withdraw-reason"
            className="form-textarea"
            placeholder="e.g., Candidate accepted another position, candidate requested withdrawal, submitted by mistake..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            disabled={isSubmitting}
            style={{ fontSize: '0.88rem' }}
          />
        </div>
      </form>
    </Modal>
  );
};
