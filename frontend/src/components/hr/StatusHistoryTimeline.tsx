import React from 'react';
import { StatusHistory } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { Clock, ArrowRight, User } from 'lucide-react';

interface StatusHistoryTimelineProps {
  history: StatusHistory[];
}

export const StatusHistoryTimeline: React.FC<StatusHistoryTimelineProps> = ({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem', fontStyle: 'italic' }}>
        No status transitions recorded yet.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', position: 'relative' }}>
      {history.map((item, idx) => (
        <div
          key={item.id}
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '14px',
            position: 'relative',
          }}
        >
          {/* Timeline Dot & Line */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '24px' }}>
            <div
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: idx === 0 ? 'var(--primary-500)' : '#475569',
                boxShadow: idx === 0 ? '0 0 10px rgba(59, 130, 246, 0.8)' : 'none',
                marginTop: '6px',
              }}
            />
            {idx < history.length - 1 && (
              <div
                style={{
                  width: '2px',
                  flex: 1,
                  minHeight: '36px',
                  background: 'var(--border-subtle)',
                  marginTop: '4px',
                }}
              />
            )}
          </div>

          {/* Details */}
          <div
            style={{
              flex: 1,
              background: 'rgba(15, 19, 29, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {item.old_status && (
                  <>
                    <StatusBadge status={item.old_status} />
                    <ArrowRight size={14} color="#64748b" />
                  </>
                )}
                <StatusBadge status={item.new_status} />
              </div>

              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} />
                {new Date(item.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
              </span>
            </div>

            {item.comment && (
              <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {item.comment}
              </p>
            )}

            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <User size={12} />
              Changed by: <span style={{ color: 'var(--text-secondary)' }}>{item.changed_by_name || 'System / Admin'}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
