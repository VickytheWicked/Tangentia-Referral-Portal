import React, { useState } from 'react';
import {
  Download,
  Briefcase,
  GraduationCap,
  Award,
  FolderGit2,
  Calendar,
  User,
  History,
  CheckCircle2,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { HistoricalCandidateItem } from '../../types/historical_suggestions';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';

interface HistoricalCandidateDetailModalProps {
  candidate: HistoricalCandidateItem;
  currentPositionTitle: string;
  onClose: () => void;
}

export const HistoricalCandidateDetailModal: React.FC<HistoricalCandidateDetailModalProps> = ({
  candidate,
  currentPositionTitle,
  onClose,
}) => {
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadCV = async () => {
    try {
      setIsDownloading(true);
      setDownloadError(null);
      await api.downloadCV(candidate.referral_id, candidate.original_filename);
    } catch (err: any) {
      setDownloadError(err.message || 'Failed to download original CV.');
    } finally {
      setIsDownloading(false);
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

  const relBadge = getRelevanceBadgeStyle(candidate.relevance_category);

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Candidate Profile: ${candidate.candidate_name}`}
      maxWidth="860px"
      footer={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Original CV: <strong style={{ color: 'var(--text-secondary)' }}>{candidate.original_filename}</strong>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={handleDownloadCV}
              disabled={isDownloading}
              className="btn btn-primary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Download size={14} className={isDownloading ? 'spin' : ''} />
              <span>{isDownloading ? 'Downloading...' : 'View Original CV'}</span>
            </button>
            <button onClick={onClose} className="btn btn-secondary btn-sm">
              Close
            </button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {downloadError && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#f87171',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              fontSize: '0.85rem',
            }}
          >
            {downloadError}
          </div>
        )}

        {/* 1. Historical Provenance Banner (Strict Labeling) */}
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(79, 70, 229, 0.15))',
            border: '1px solid rgba(139, 92, 246, 0.35)',
            borderRadius: '10px',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  padding: '3px 10px',
                  borderRadius: '20px',
                  background: 'rgba(139, 92, 246, 0.25)',
                  color: '#c4b5fd',
                  border: '1px solid rgba(139, 92, 246, 0.45)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                }}
              >
                <History size={13} />
                OLD REFERRAL
              </span>
              <span
                style={{
                  fontSize: '0.74rem',
                  fontWeight: 700,
                  padding: '3px 10px',
                  borderRadius: '20px',
                  background: relBadge.bg,
                  color: relBadge.color,
                  border: `1px solid ${relBadge.border}`,
                }}
              >
                {candidate.relevance_category}
              </span>
            </div>

            <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
              Original Status:{' '}
              <span style={{ fontWeight: 600, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                {candidate.original_status}
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '0.84rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Previously referred for:</span>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                {candidate.original_position_title}
              </div>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)' }}>Original Referral Number:</span>
              <div style={{ fontWeight: 700, color: '#93c5fd', marginTop: '2px', fontFamily: 'monospace' }}>
                {candidate.referral_number}
              </div>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)' }}>Original Referral Date:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                {candidate.original_referral_date || 'Previous Requisition'}
              </div>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)' }}>Referring Employee:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                {candidate.referred_by_name}
              </div>
            </div>
          </div>
        </div>

        {/* 2. Why this candidate is relevant to current opening */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Why this candidate is relevant to{' '}
              <span style={{ color: 'var(--primary)' }}>{currentPositionTitle}</span>:
            </h4>
            <span style={{ fontSize: '0.78rem', color: '#93c5fd', fontWeight: 600 }}>
              {candidate.experience_summary}
            </span>
          </div>

          {candidate.fit_narrative && (
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {candidate.fit_narrative}
            </p>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
            {candidate.relevance_reasons.map((reason, rIdx) => {
              const isMatch = reason.startsWith('✓');
              return (
                <div
                  key={rIdx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.84rem',
                    color: isMatch ? '#34d399' : 'var(--text-secondary)',
                    fontWeight: isMatch ? 600 : 400,
                  }}
                >
                  <span>{reason}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. Candidate Skills */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div>
            <h5 style={{ margin: '0 0 10px 0', fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Historical Candidate Skills ({candidate.skills.length})
            </h5>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {candidate.skills.map((skill, sIdx) => {
                const isMatched = candidate.matched_skills.some(
                  (m) => m.toLowerCase() === skill.toLowerCase()
                );
                return (
                  <span
                    key={sIdx}
                    style={{
                      fontSize: '0.76rem',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontWeight: isMatched ? 700 : 500,
                      background: isMatched ? 'rgba(16, 185, 129, 0.15)' : 'rgba(30, 41, 59, 0.6)',
                      color: isMatched ? '#34d399' : 'var(--text-secondary)',
                      border: `1px solid ${isMatched ? 'rgba(16, 185, 129, 0.4)' : 'rgba(148, 163, 184, 0.2)'}`,
                    }}
                  >
                    {isMatched ? '✓ ' : ''}{skill}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. Experience History */}
        {candidate.experience && candidate.experience.length > 0 && (
          <div>
            <h5 style={{ margin: '0 0 12px 0', fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Briefcase size={16} color="var(--primary)" /> Career History
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {candidate.experience.map((exp, eIdx) => (
                <div
                  key={eIdx}
                  style={{
                    background: 'var(--bg-secondary)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                      {exp.job_title || 'Role'}
                    </div>
                    {exp.duration && (
                      <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                        {exp.duration}
                      </span>
                    )}
                  </div>
                  {exp.company && (
                    <div style={{ fontSize: '0.82rem', color: '#93c5fd', marginTop: '2px', fontWeight: 600 }}>
                      {exp.company}
                    </div>
                  )}
                  {exp.responsibilities && exp.responsibilities.length > 0 && (
                    <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {exp.responsibilities.map((resp, rIdx) => (
                        <li key={rIdx}>{resp}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5. Projects */}
        {candidate.projects && candidate.projects.length > 0 && (
          <div>
            <h5 style={{ margin: '0 0 12px 0', fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FolderGit2 size={16} color="var(--primary)" /> Notable Projects
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {candidate.projects.map((proj, pIdx) => (
                <div
                  key={pIdx}
                  style={{
                    background: 'var(--bg-secondary)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                    {proj.name || 'Project'}
                  </div>
                  {proj.description && (
                    <p style={{ margin: '4px 0 6px 0', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                      {proj.description}
                    </p>
                  )}
                  {proj.technologies && proj.technologies.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {proj.technologies.map((t, tIdx) => (
                        <span
                          key={tIdx}
                          style={{
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            background: 'rgba(59, 130, 246, 0.15)',
                            color: '#93c5fd',
                          }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 6. Education & Certifications */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '16px' }}>
          {candidate.education && candidate.education.length > 0 && (
            <div>
              <h5 style={{ margin: '0 0 10px 0', fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GraduationCap size={16} color="var(--primary)" /> Education
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {candidate.education.map((edu, edIdx) => (
                  <div key={edIdx} style={{ background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                      {edu.degree || edu.field_of_study || 'Degree'}
                    </div>
                    {edu.institution && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {edu.institution} {edu.graduation_year ? `(${edu.graduation_year})` : ''}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {candidate.certifications && candidate.certifications.length > 0 && (
            <div>
              <h5 style={{ margin: '0 0 10px 0', fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Award size={16} color="var(--primary)" /> Certifications
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {candidate.certifications.map((cert, cIdx) => (
                  <div key={cIdx} style={{ background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                      {cert.name}
                    </div>
                    {cert.issuer && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {cert.issuer} {cert.year ? `(${cert.year})` : ''}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};
