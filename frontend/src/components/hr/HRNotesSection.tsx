import React, { useState } from 'react';
import { HRNote } from '../../types';
import { api } from '../../services/api';
import { MessageSquare, Plus, Lock } from 'lucide-react';

interface HRNotesSectionProps {
  referralId: string;
  notes: HRNote[];
  onNoteAdded: () => void;
}

export const HRNotesSection: React.FC<HRNotesSectionProps> = ({
  referralId,
  notes,
  onNoteAdded,
}) => {
  const [newNote, setNewNote] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await api.addHRNote(referralId, newNote.trim());
      setNewNote('');
      onNoteAdded();
    } catch (err: any) {
      setError(err.message || 'Failed to save note');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lock size={16} color="#94a3b8" />
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Confidential Internal HR Notes
          </h4>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
          HR Eyes Only
        </span>
      </div>

      <form onSubmit={handleAddNote} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {error && (
          <div style={{ color: '#ef4444', fontSize: '0.82rem' }}>{error}</div>
        )}
        <textarea
          className="form-textarea"
          placeholder="Add confidential candidate evaluation notes, compensation expectations, or interview feedback..."
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          rows={3}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            className="btn btn-primary btn-sm"
            disabled={isSubmitting || !newNote.trim()}
          >
            <Plus size={14} />
            {isSubmitting ? 'Adding...' : 'Add Note'}
          </button>
        </div>
      </form>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '6px' }}>
        {notes.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem', fontStyle: 'italic', padding: '12px 0' }}>
            No internal notes have been recorded for this referral yet.
          </div>
        ) : (
          notes.map((n) => (
            <div
              key={n.id}
              style={{
                background: 'rgba(15, 19, 29, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#93c5fd' }}>
                  {n.created_by_name || 'HR Team Member'}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(n.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                </span>
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                {n.note}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
