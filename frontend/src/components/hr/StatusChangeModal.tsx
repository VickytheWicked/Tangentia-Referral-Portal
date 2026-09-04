import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { ReferralStatusType } from '../../types';
import { api } from '../../services/api';
import { RefreshCw, CheckCircle2 } from 'lucide-react';

interface StatusChangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  referralId: string;
  candidateName: string;
  currentStatus: ReferralStatusType;
  onStatusUpdated: () => void;
}

const ALL_STATUSES: ReferralStatusType[] = [
  'Submitted',
  'Under Review',
  'Shortlisted',
  'Interview',
  'Selected',
  'Hired',
  'Rejected',
  'Withdrawn',
];

export const StatusChangeModal: React.FC<StatusChangeModalProps> = ({
  isOpen,
  onClose,
  referralId,
  candidateName,
  currentStatus,
  onStatusUpdated,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<ReferralStatusType>(currentStatus);
  const [comment, setComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await api.updateStatus(referralId, selectedStatus, comment);
      onStatusUpdated();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update status.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Update Status: ${candidateName}`}
      maxWidth="500px"
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={isSubmitting || selectedStatus === currentStatus}
          >
            {isSubmitting ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <CheckCircle2 size={16} />
                Save New Status
              </>
            )}
          </button>
        </>
      }
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <div style={{ color: '#ef4444', marginBottom: '14px', fontSize: '0.86rem', background: 'rgba(239, 68, 68, 0.1)', padding: '10px 14px', borderRadius: '8px' }}>
            {error}
          </div>
        )}

        <div className="form-group">
          <label className="form-label">New Status</label>
          <select
            className="form-select"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value as ReferralStatusType)}
          >
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s} {s === currentStatus ? '(Current)' : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Audit Note / Comment (Optional)</label>
          <textarea
            className="form-textarea"
            placeholder="e.g. Cleared round 1 technical interview, advancing to panel review."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <span className="form-hint">
            This comment will be permanently recorded in the candidate's referral audit log.
          </span>
        </div>
      </form>
    </Modal>
  );
};
