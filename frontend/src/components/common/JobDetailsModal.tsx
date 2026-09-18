import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { JobPosition } from '../../types';
import { Modal } from './Modal';
import { JobUnavailableModal } from './JobUnavailableModal';
import { api } from '../../services/api';
import {
  Briefcase,
  MapPin,
  Clock,
  Building,
  ExternalLink,
  PlusCircle,
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';

interface JobDetailsModalProps {
  job: JobPosition | null;
  isOpen: boolean;
  onClose: () => void;
  showReferButton?: boolean;
  onRefer?: (job: JobPosition) => void;
}

export const JobDetailsModal: React.FC<JobDetailsModalProps> = ({
  job,
  isOpen,
  onClose,
  showReferButton = true,
  onRefer,
}) => {
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [isUnavailableModalOpen, setIsUnavailableModalOpen] = useState<boolean>(false);

  if (!job) return null;

  const isCatsJob = job.id.startsWith('cats-');
  const catsJobId = isCatsJob ? job.id.replace('cats-', '') : null;
  const catsDirectUrl = catsJobId
    ? `https://tangentia.catsone.com/careers/9463/jobs/${catsJobId}`
    : 'https://tangentia.catsone.com/careers/9463-General';

  // Format description paragraphs and bullet points cleanly
  const renderFormattedDescription = (text: string) => {
    if (!text) {
      return (
        <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
          No extended job description provided.
        </p>
      );
    }

    const lines = text.split('\n');
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {lines.map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) {
            return <div key={idx} style={{ height: '6px' }} />;
          }

          // Header lines (e.g. Key Responsibilities:, Requirements:, Job Summary:)
          const isHeader =
            /^(key responsibilities|responsibilities|required qualifications|qualifications|required skills|skills|job summary|role overview|position summary|overview|requirements|about the role):?$/i.test(
              trimmed
            );

          if (isHeader) {
            return (
              <h5
                key={idx}
                style={{
                  fontSize: '0.94rem',
                  fontWeight: 700,
                  color: '#93c5fd',
                  marginTop: '10px',
                  marginBottom: '2px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                {trimmed}
              </h5>
            );
          }

          // Bullet points
          if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                  paddingLeft: '4px',
                  color: 'var(--text-secondary)',
                  fontSize: '0.88rem',
                  lineHeight: 1.6,
                }}
              >
                <span style={{ color: '#60a5fa', fontWeight: 700 }}>•</span>
                <span>{trimmed.replace(/^[•\-\*]\s*/, '')}</span>
              </div>
            );
          }

          // Standard paragraph
          return (
            <p
              key={idx}
              style={{
                color: 'var(--text-secondary)',
                fontSize: '0.88rem',
                lineHeight: 1.6,
                margin: 0,
              }}
            >
              {trimmed}
            </p>
          );
        })}
      </div>
    );
  };

  const handleReferClick = async () => {
    if (onRefer) {
      onRefer(job);
      return;
    }
    setIsChecking(true);
    try {
      const liveJob = await api.getJob(job.id);
      if (!liveJob || !liveJob.is_active) {
        setIsUnavailableModalOpen(true);
        return;
      }
      onClose();
      navigate(`/employee/submit?positionId=${encodeURIComponent(job.id)}`, {
        state: { positionId: job.id },
      });
    } catch {
      setIsUnavailableModalOpen(true);
    } finally {
      setIsChecking(false);
    }
  };

  const modalFooter = (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        gap: '12px',
        flexWrap: 'wrap',
      }}
    >
      <div>
        {isCatsJob && (
          <a
            href={catsDirectUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}
          >
            <ExternalLink size={14} /> Open in Tangentia CATS One
          </a>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
          Close
        </button>
        {showReferButton && job.is_active && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleReferClick}
            disabled={isChecking}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            {isChecking ? <Loader2 size={15} className="spin" /> : <PlusCircle size={15} />}
            {isChecking ? 'Checking status...' : 'Refer Candidate'}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      <Modal
        isOpen={isOpen && !isUnavailableModalOpen}
        onClose={onClose}
        title={job.title}
        maxWidth="720px"
        footer={modalFooter}
      >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Top Badges & Context */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            flexWrap: 'wrap',
            padding: '12px 16px',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                color: '#60a5fa',
                background: 'rgba(59, 130, 246, 0.15)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                padding: '3px 10px',
                borderRadius: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {job.department}
            </span>

            {isCatsJob && (
              <span
                style={{
                  fontSize: '0.74rem',
                  fontWeight: 700,
                  color: '#93c5fd',
                  background: 'rgba(59, 130, 246, 0.12)',
                  border: '1px solid rgba(59, 130, 246, 0.25)',
                  padding: '3px 10px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                CATS ATS Requisition
              </span>
            )}
          </div>

          <span
            style={{
              fontSize: '0.76rem',
              fontWeight: 600,
              padding: '4px 10px',
              borderRadius: '12px',
              background: job.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: job.is_active ? '#34d399' : '#f87171',
              border: `1px solid ${job.is_active ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            {job.is_active ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
            {job.is_active ? 'Active Opening' : 'Deactivated / Closed'}
          </span>
        </div>

        {/* Overview Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
          }}
        >
          <div
            style={{
              padding: '12px 14px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <MapPin size={18} color="#60a5fa" />
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Location
              </div>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {job.location}
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '12px 14px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <Clock size={18} color="#60a5fa" />
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Employment Type
              </div>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {job.employment_type}
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '12px 14px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <Briefcase size={18} color="#60a5fa" />
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Position ID
              </div>
              <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                {job.id}
              </div>
            </div>
          </div>
        </div>

        {/* Full Details Section */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <FileText size={16} color="#60a5fa" />
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Extracted Position Details & Responsibilities
            </h4>
          </div>

          <div
            style={{
              padding: '16px',
              background: 'var(--bg-main)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              maxHeight: '380px',
              overflowY: 'auto',
            }}
          >
            {renderFormattedDescription(job.description)}
          </div>
        </div>
      </div>
    </Modal>

    <JobUnavailableModal
      isOpen={isUnavailableModalOpen}
      onClose={() => {
        setIsUnavailableModalOpen(false);
        onClose();
      }}
      jobTitle={job.title}
      onExploreOtherJobs={() => {
        setIsUnavailableModalOpen(false);
        onClose();
        navigate('/employee/openings');
      }}
    />
    </>
  );
};
