import React, { useState, useEffect } from 'react';
import {
  History,
  Sparkles,
  Download,
  Eye,
  Briefcase,
  Calendar,
  User,
  CheckCircle2,
  RefreshCw,
  Search,
  ExternalLink,
} from 'lucide-react';
import { HistoricalCandidateItem, HistoricalSuggestionsResponse } from '../../types/historical_suggestions';
import { api } from '../../services/api';
import { HistoricalCandidateDetailModal } from './HistoricalCandidateDetailModal';

interface HistoricalReferralsSectionProps {
  positionId: string;
  currentPositionTitle: string;
}

export const HistoricalReferralsSection: React.FC<HistoricalReferralsSectionProps> = ({
  positionId,
  currentPositionTitle,
}) => {
  const [data, setData] = useState<HistoricalSuggestionsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<HistoricalCandidateItem | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [isDisabled, setIsDisabled] = useState<boolean>(false);

  const fetchHistorical = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getHistoricalSuggestions(positionId);
      setData(res);
    } catch (err: any) {
      if (err.message && (err.message.includes('disabled') || err.message.includes('404'))) {
        setIsDisabled(true);
      } else {
        setError(err.message || 'Failed to load historical candidate suggestions.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistorical();
  }, [positionId]);

  if (isDisabled) {
    return null; // Feature is disabled, do not render
  }

  const handleDownloadCV = async (e: React.MouseEvent, candidate: HistoricalCandidateItem) => {
    e.stopPropagation();
    try {
      setDownloadingId(candidate.referral_id);
      await api.downloadCV(candidate.referral_id, candidate.original_filename);
    } catch (err: any) {
      alert(`Failed to download CV: ${err.message || 'Unknown error'}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const getRelevanceBadgeStyle = (category: string) => {
    if (category === 'Strong Relevance') {
      return { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.35)' };
    }
    if (category === 'Good Relevance') {
      return { bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.35)' };
    }
    return { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.35)' };
  };

  return (
    <div
      style={{
        marginTop: '28px',
        paddingTop: '24px',
        borderTop: '2px dashed rgba(139, 92, 246, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 800,
                letterSpacing: '0.07em',
                textTransform: 'uppercase',
                padding: '3px 10px',
                borderRadius: '20px',
                background: 'rgba(139, 92, 246, 0.2)',
                color: '#c4b5fd',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
              }}
            >
              <History size={13} />
              OLD REFERRALS
            </span>
            <h5 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Previously Submitted Candidates (Archived Requisitions)
            </h5>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Archived candidates from other closed openings whose profiles appear relevant to this opening via semantic search
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-outline btn-sm"
            onClick={fetchHistorical}
            disabled={loading}
            style={{ fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: '5px' }}
            title="Refresh historical suggestions"
          >
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
            <span>Search Pool</span>
          </button>
          {data && (
            <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              Found <strong>{data.suggestions.length}</strong> matching candidate{data.suggestions.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Advisory Banner explaining historical nature */}
      <div
        style={{
          background: 'rgba(139, 92, 246, 0.08)',
          border: '1px solid rgba(139, 92, 246, 0.22)',
          borderRadius: '8px',
          padding: '10px 16px',
          fontSize: '0.8rem',
          color: '#cbd5e1',
          lineHeight: '1.45',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <Sparkles size={16} color="#a78bfa" style={{ flexShrink: 0 }} />
        <div>
          <strong style={{ color: '#c4b5fd' }}>Historical Provenance Preserved:</strong> These candidates were
          originally referred for other job openings that were closed. They remain securely archived under their original
          referrals. No new referral is created.
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
          <RefreshCw size={20} className="spin" style={{ margin: '0 auto 8px', display: 'block', opacity: 0.6 }} />
          Searching archived referrals for semantic relevance...
        </div>
      ) : error ? (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.15)',
            color: '#f87171',
            fontSize: '0.84rem',
            border: '1px solid rgba(239, 68, 68, 0.3)',
          }}
        >
          {error}
        </div>
      ) : !data || data.suggestions.length === 0 ? (
        <div
          style={{
            padding: '24px',
            textAlign: 'center',
            background: 'rgba(15, 23, 42, 0.4)',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}
        >
          No historical archived candidates currently meet the relevance threshold for this job opening.
        </div>
      ) : (
        /* Candidates List */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {data.suggestions.map((cand) => {
            const relBadge = getRelevanceBadgeStyle(cand.relevance_category);

            return (
              <div
                key={cand.referral_id}
                onClick={() => setSelectedCandidate(cand)}
                style={{
                  background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.75))',
                  border: '1px solid rgba(139, 92, 246, 0.25)',
                  borderRadius: '10px',
                  padding: '16px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  cursor: 'pointer',
                  transition: 'border-color 0.15s ease, transform 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.55)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.25)';
                }}
              >
                {/* Header Row */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 800,
                          letterSpacing: '0.05em',
                          textTransform: 'uppercase',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          background: 'rgba(139, 92, 246, 0.25)',
                          color: '#c4b5fd',
                          border: '1px solid rgba(139, 92, 246, 0.45)',
                        }}
                      >
                        OLD REFERRAL
                      </span>

                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '12px',
                          background: relBadge.bg,
                          color: relBadge.color,
                          border: `1px solid ${relBadge.border}`,
                        }}
                      >
                        {cand.relevance_category}
                      </span>

                      <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                        {cand.referral_number}
                      </span>
                    </div>

                    <h4 style={{ margin: '6px 0 2px 0', fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {cand.candidate_name}
                    </h4>

                    <div style={{ fontSize: '0.8rem', color: '#93c5fd', marginTop: '2px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Previously referred for: </span>
                      <strong>{cand.original_position_title}</strong>
                      {cand.original_referral_date && (
                        <span style={{ color: 'var(--text-muted)' }}> • {cand.original_referral_date}</span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => setSelectedCandidate(cand)}
                      style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '5px' }}
                    >
                      <Eye size={13} /> View Profile
                    </button>

                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={(e) => handleDownloadCV(e, cand)}
                      disabled={downloadingId === cand.referral_id}
                      style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '5px' }}
                      title="Download candidate's original CV"
                    >
                      <Download size={13} className={downloadingId === cand.referral_id ? 'spin' : ''} />
                      <span>{downloadingId === cand.referral_id ? 'Downloading...' : 'View Original CV'}</span>
                    </button>
                  </div>
                </div>

                {/* Candidate Relevant Information Summary */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  {cand.skills && cand.skills.length > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                      {cand.skills.slice(0, 5).map((skill, sIdx) => {
                        const isMatch = cand.matched_skills.some(
                          (m) => m.toLowerCase() === skill.toLowerCase()
                        );
                        return (
                          <span
                            key={sIdx}
                            style={{
                              fontSize: '0.74rem',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontWeight: isMatch ? 700 : 500,
                              background: isMatch ? 'rgba(16, 185, 129, 0.15)' : 'rgba(30, 41, 59, 0.8)',
                              color: isMatch ? '#34d399' : 'var(--text-secondary)',
                              border: `1px solid ${isMatch ? 'rgba(16, 185, 129, 0.35)' : 'rgba(148, 163, 184, 0.2)'}`,
                            }}
                          >
                            {isMatch ? '✓ ' : ''}{skill}
                          </span>
                        );
                      })}
                      {cand.skills.length > 5 && (
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          +{cand.skills.length - 5} more
                        </span>
                      )}
                    </div>
                  )}

                  <span>•</span>
                  <span>{cand.experience_summary}</span>

                  <span>•</span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    Referred by: <strong style={{ color: 'var(--text-secondary)' }}>{cand.referred_by_name}</strong>
                  </span>
                </div>

                {/* Decision Highlights */}
                {cand.relevance_reasons && cand.relevance_reasons.length > 0 && (
                  <div
                    style={{
                      background: 'rgba(15, 23, 42, 0.45)',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      flexWrap: 'wrap',
                      fontSize: '0.78rem',
                    }}
                  >
                    {cand.relevance_reasons.map((reason, rIdx) => {
                      const isMatch = reason.startsWith('✓');
                      return (
                        <span
                          key={rIdx}
                          style={{
                            color: isMatch ? '#34d399' : 'var(--text-muted)',
                            fontWeight: isMatch ? 600 : 400,
                          }}
                        >
                          {reason}
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Profile Detail Modal */}
      {selectedCandidate && (
        <HistoricalCandidateDetailModal
          candidate={selectedCandidate}
          currentPositionTitle={currentPositionTitle}
          onClose={() => setSelectedCandidate(null)}
        />
      )}
    </div>
  );
};
