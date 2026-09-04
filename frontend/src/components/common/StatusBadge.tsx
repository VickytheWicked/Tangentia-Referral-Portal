import React from 'react';
import { ReferralStatusType } from '../../types';

interface StatusBadgeProps {
  status: ReferralStatusType | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getBadgeClass = (s: string) => {
    switch (s) {
      case 'Submitted':
        return 'badge-submitted';
      case 'Under Review':
        return 'badge-under-review';
      case 'Shortlisted':
        return 'badge-shortlisted';
      case 'Interview':
        return 'badge-interview';
      case 'Selected':
        return 'badge-selected';
      case 'Hired':
        return 'badge-hired';
      case 'Rejected':
        return 'badge-rejected';
      case 'Withdrawn':
        return 'badge-withdrawn';
      case 'Archived':
        return 'badge-archived';
      default:
        return 'badge-submitted';
    }
  };

  return (
    <span className={`badge ${getBadgeClass(status)}`}>
      <span className="badge-dot" />
      {status}
    </span>
  );
};
