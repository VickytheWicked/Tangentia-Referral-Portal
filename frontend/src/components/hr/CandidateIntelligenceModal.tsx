import React, { useState } from 'react';
import {
  Download,
  Briefcase,
  GraduationCap,
  Award,
  FolderGit2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Layers,
  Building,
  Calendar,
  Edit3,
} from 'lucide-react';
import { CandidateProfileDetail } from '../../types/cv_intelligence';
import { ReferralStatusType } from '../../types';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { StatusBadge } from '../common/StatusBadge';
import { StatusChangeModal } from './StatusChangeModal';
import { AIRequirementAnalysisSection } from './AIRequirementAnalysisSection';

interface CandidateIntelligenceModalProps {
  profile: CandidateProfileDetail;
  onClose: () => void;
  onProfileUpdated?: (updated: CandidateProfileDetail) => void;
}

export const CandidateIntelligenceModal: React.FC<CandidateIntelligenceModalProps> = ({
  profile: initialProfile,
  onClose,
  onProfileUpdated,
}) => {
  const [profile, setProfile] = useState<CandidateProfileDetail>(initialProfile);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleDownloadCV = async () => {
    try {
      setIsDownloading(true);
      setErrorMsg(null);
      await api.downloadCV(profile.referral_id, profile.original_filename);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to download original CV.');
    } finally {
      setIsDownloading(false);
    }
  };

  const getMatchBadgeStyle = (level?: string) => {
    if (level === 'Strong Match') return { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.3)' };
    if (level === 'Good Match') return { bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)' };
    if (level === 'Potential Match') return { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)' };
    if (profile.extraction_status === 'FAILED') return { bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: 'rgba(239, 68, 68, 0.3)' };
    return { bg: 'rgba(100, 116, 139, 0.15)', color: '#94a3b8', border: 'rgba(100, 116, 139, 0.3)' };
  };

  const matchStyle = getMatchBadgeStyle(profile.match?.match_level);

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Candidate Profile: ${profile.candidate_name || 'Candidate'}`}
      maxWidth="850px"
      footer={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Original CV: <strong style={{ color: 'var(--text-secondary)' }}>{profile.original_filename}</strong>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={() => setIsStatusModalOpen(true)}
              className="btn btn-secondary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Change Candidate Status"
            >
              <Edit3 size={14} />
              <span>Change Status</span>
            </button>
            <button
              onClick={handleDownloadCV}
              disabled={isDownloading}
              className="btn btn-primary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Download size={14} />
              <span>{isDownloading ? 'Downloading...' : 'Download Original CV'}</span>
            </button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {errorMsg && (
          <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.86rem' }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Header Summary */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
            padding: '18px 20px',
            background: 'var(--bg-secondary)',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div>
            {profile.referral_number && (
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {profile.referral_number}
              </div>
            )}
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)', margin: '4px 0' }}>
              {profile.candidate_name || 'Candidate'}
            </h3>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              {profile.position_title}
            </div>
          </div>

          <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {profile.match?.match_level && (
                <span
                  style={{
                    fontSize: '0.78rem',
                    padding: '3px 10px',
                    borderRadius: '12px',
                    background: matchStyle.bg,
                    color: matchStyle.color,
                    border: `1px solid ${matchStyle.border}`,
                    fontWeight: 700,
                  }}
                >
                  {profile.match.match_level}
                </span>
              )}
              <StatusBadge status={profile.referral_status} />
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setIsStatusModalOpen(true)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '3px 8px',
                  fontSize: '0.74rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  background: 'rgba(59, 130, 246, 0.12)',
                  color: '#93c5fd',
                  cursor: 'pointer',
                  marginLeft: '4px',
                }}
                title="Change Candidate Status"
              >
                <Edit3 size={12} />
                <span>Change Status</span>
              </button>
            </div>
            {profile.created_at && (
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                Submitted: {new Date(profile.created_at).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>

        {/* Candidate & Referrer Info Grid (Manage Profile Details) */}
        <div
          className="responsive-info-grid"
          style={{
            gap: '14px',
            background: 'rgba(15, 19, 29, 0.4)',
            padding: '16px',
            borderRadius: '10px',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.86rem',
          }}
        >
          <div><strong>Email:</strong> {profile.email || 'N/A'}</div>
          <div><strong>Phone:</strong> {profile.phone || 'N/A'}</div>
          <div><strong>Experience:</strong> {profile.years_of_experience || 0} years</div>
          {profile.referred_by_name && (
            <div>
              <strong>Referred by:</strong> {profile.referred_by_name} {profile.relationship ? `(${profile.relationship})` : ''}
            </div>
          )}
          {profile.referred_by_email && (
            <div><strong>Referrer Email:</strong> {profile.referred_by_email}</div>
          )}
          <div>
            <strong>CV Storage:</strong> SharePoint Online ({profile.original_filename})
          </div>
          {profile.linkedin_url && (
            <div>
              <strong>LinkedIn:</strong>{' '}
              <a href={profile.linkedin_url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>
                View Profile
              </a>
            </div>
          )}
          {profile.github_url && (
            <div>
              <strong>GitHub:</strong>{' '}
              <a href={profile.github_url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>
                View Portfolio
              </a>
            </div>
          )}
        </div>

        {/* Referring Employee Recommendation Note */}
        {profile.referral_note && (
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Referring Employee Recommendation Note:
            </h4>
            <div
              style={{
                background: 'rgba(15, 19, 29, 0.4)',
                padding: '14px 16px',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.88rem',
                lineHeight: 1.5,
                color: 'var(--text-secondary)',
              }}
            >
              {profile.referral_note}
            </div>
          </div>
        )}

        {/* CV Intelligence: AI Requirement Analysis */}
        {profile.match?.requirement_analysis ? (
          <AIRequirementAnalysisSection
            analysis={profile.match.requirement_analysis}
            candidateName={profile.candidate_name || undefined}
            positionTitle={profile.position_title || undefined}
          />
        ) : (
          /* Legacy fallback — shown for candidates not yet reprocessed with the new pipeline */
          <div
            style={{
              background: 'rgba(30, 58, 138, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              borderRadius: '10px',
              padding: '16px 18px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Sparkles size={18} color="#60a5fa" />
              <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#93c5fd' }}>
                Relevance &amp; Requirement Alignment
              </h4>
            </div>

            {profile.match?.fit_summary && (
              <div
                style={{
                  marginBottom: '14px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(59, 130, 246, 0.12)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  fontSize: '0.88rem',
                  lineHeight: 1.5,
                  color: '#e0f2fe',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                }}
              >
                <Sparkles size={15} color="#38bdf8" style={{ marginTop: '3px', flexShrink: 0 }} />
                <div>
                  <strong style={{ color: '#93c5fd' }}>AI Fit Summary: </strong>
                  <span style={{ fontStyle: 'italic' }}>{profile.match.fit_summary}</span>
                </div>
              </div>
            )}

            {profile.match && profile.match.explanation && profile.match.explanation.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {profile.match.explanation.map((item, idx) => {
                  const isCheck = item.startsWith('✓');
                  return (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px',
                        fontSize: '0.88rem',
                        color: isCheck ? '#34d399' : 'var(--text-muted)',
                      }}
                    >
                      {isCheck ? (
                        <CheckCircle2 size={15} color="#34d399" style={{ marginTop: '2px', flexShrink: 0 }} />
                      ) : (
                        <span style={{ width: '15px', textAlign: 'center', color: '#94a3b8', flexShrink: 0 }}>•</span>
                      )}
                      <span>{item.replace(/^[✓•]\s*/, '')}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-muted)' }}>
                {profile.extraction_status === 'COMPLETED'
                  ? 'Candidate profile parsed successfully.'
                  : 'CV extraction is pending or not yet processed.'}
              </p>
            )}

            {/* Matched & Missing Skills Badges */}
            {profile.match && (
              <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(59, 130, 246, 0.15)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {profile.match.matched_skills.length > 0 && (
                  <div>
                    <span style={{ fontSize: '0.76rem', textTransform: 'uppercase', fontWeight: 700, color: '#34d399', letterSpacing: '0.5px' }}>
                      Matched Skills:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                      {profile.match.matched_skills.map((s, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '0.78rem',
                            padding: '2px 8px',
                            borderRadius: '10px',
                            background: 'rgba(16, 185, 129, 0.15)',
                            color: '#34d399',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            fontWeight: 600,
                          }}
                        >
                          ✓ {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {profile.match.missing_skills.length > 0 && (
                  <div>
                    <span style={{ fontSize: '0.76rem', textTransform: 'uppercase', fontWeight: 700, color: '#fbbf24', letterSpacing: '0.5px' }}>
                      Missing / Unmentioned Requirements:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                      {profile.match.missing_skills.map((m, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '0.78rem',
                            padding: '2px 8px',
                            borderRadius: '10px',
                            background: 'rgba(245, 158, 11, 0.15)',
                            color: '#fbbf24',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                            fontWeight: 600,
                          }}
                        >
                          • {m}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Extracted Skills Section */}
        {profile.skills && profile.skills.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={15} color="var(--primary)" />
              Extracted Resume Skills ({profile.skills.length})
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {profile.skills.map((skill, index) => (
                <span
                  key={index}
                  style={{
                    fontSize: '0.8rem',
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Work Experience */}
        {profile.experience && profile.experience.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Briefcase size={15} color="var(--primary)" />
              Work Experience
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {profile.experience.map((exp, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '8px',
                    background: 'rgba(15, 19, 29, 0.4)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                      {exp.job_title || 'Role'} {exp.company ? `• ${exp.company}` : ''}
                    </div>
                    {exp.duration && (
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {exp.duration}
                      </span>
                    )}
                  </div>
                  {exp.responsibilities && exp.responsibilities.length > 0 && (
                    <ul style={{ margin: '6px 0 0 0', paddingLeft: '18px', fontSize: '0.84rem', color: 'var(--text-muted)' }}>
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

        {/* Projects */}
        {profile.projects && profile.projects.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FolderGit2 size={15} color="var(--primary)" />
              Key Projects
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '10px' }}>
              {profile.projects.map((proj, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'rgba(15, 19, 29, 0.4)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)', marginBottom: '4px' }}>
                    {proj.name || 'Project'}
                  </div>
                  {proj.description && (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                      {proj.description}
                    </p>
                  )}
                  {proj.technologies && proj.technologies.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                      {proj.technologies.map((t, tIdx) => (
                        <span
                          key={tIdx}
                          style={{
                            fontSize: '0.72rem',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-secondary)',
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

        {/* Education & Certifications Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <GraduationCap size={15} color="var(--primary)" />
              Education {profile.education && profile.education.length > 0 ? `(${profile.education.length})` : ''}
            </h4>
            {profile.education && profile.education.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {profile.education.map((edu, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(15, 19, 29, 0.4)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.88rem', lineHeight: 1.3 }}>
                        {edu.degree || 'Degree'}
                      </div>
                      {edu.graduation_year && (
                        <span
                          style={{
                            fontSize: '0.74rem',
                            padding: '1px 7px',
                            borderRadius: '10px',
                            background: 'rgba(59, 130, 246, 0.12)',
                            color: '#60a5fa',
                            border: '1px solid rgba(59, 130, 246, 0.25)',
                            fontWeight: 600,
                            whiteSpace: 'nowrap',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <Calendar size={11} />
                          {edu.graduation_year}
                        </span>
                      )}
                    </div>
                    {edu.institution && (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Building size={13} style={{ flexShrink: 0, opacity: 0.8 }} />
                        <span>{edu.institution}</span>
                      </div>
                    )}
                    {(edu.field_of_study || edu.grade_or_score) && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '3px' }}>
                        {edu.field_of_study && (
                          <span
                            style={{
                              fontSize: '0.73rem',
                              padding: '1px 6px',
                              borderRadius: '4px',
                              background: 'var(--bg-secondary)',
                              color: 'var(--text-secondary)',
                              border: '1px solid var(--border-subtle)',
                            }}
                          >
                            Major: {edu.field_of_study}
                          </span>
                        )}
                        {edu.grade_or_score && (
                          <span
                            style={{
                              fontSize: '0.73rem',
                              padding: '1px 6px',
                              borderRadius: '4px',
                              background: 'rgba(16, 185, 129, 0.12)',
                              color: '#34d399',
                              border: '1px solid rgba(16, 185, 129, 0.25)',
                              fontWeight: 600,
                            }}
                          >
                            {edu.grade_or_score}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div
                style={{
                  padding: '12px',
                  borderRadius: '6px',
                  background: 'rgba(15, 19, 29, 0.3)',
                  border: '1px dashed var(--border-subtle)',
                  color: 'var(--text-muted)',
                  fontSize: '0.82rem',
                  fontStyle: 'italic',
                }}
              >
                No explicit academic degree listed on resume
              </div>
            )}
          </div>

          {profile.certifications && profile.certifications.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Award size={15} color="var(--primary)" />
                Certifications
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {profile.certifications.map((cert, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '8px 12px',
                      borderRadius: '6px',
                      background: 'rgba(15, 19, 29, 0.4)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.84rem',
                    }}
                  >
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{cert.name || 'Certification'}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      {cert.issuer} {cert.year ? `• ${cert.year}` : ''}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {isStatusModalOpen && (
        <StatusChangeModal
          isOpen={isStatusModalOpen}
          onClose={() => setIsStatusModalOpen(false)}
          referralId={profile.referral_id}
          candidateName={profile.candidate_name || 'Candidate'}
          currentStatus={profile.referral_status as ReferralStatusType}
          onStatusUpdated={async () => {
            try {
              const updated = await api.getCandidateIntelligence(profile.referral_id);
              setProfile(updated);
              if (onProfileUpdated) {
                onProfileUpdated(updated);
              }
            } catch (err) {
              console.error('Failed to reload candidate intelligence', err);
              // Fallback update to local state
              if (onProfileUpdated) {
                onProfileUpdated(profile);
              }
            }
          }}
        />
      )}
    </Modal>
  );
};
