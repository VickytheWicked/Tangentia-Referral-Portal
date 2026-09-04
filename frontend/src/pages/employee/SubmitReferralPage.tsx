import React, { useState, useEffect, useRef } from 'react';
import { JobPosition, DuplicateMatch } from '../../types';
import { api } from '../../services/api';
import { DuplicateModal } from '../../components/common/DuplicateModal';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  X,
  ShieldCheck,
  Building2,
} from 'lucide-react';

interface SubmitReferralPageProps {
  onReferralCreated: () => void;
}

export const SubmitReferralPage: React.FC<SubmitReferralPageProps> = ({ onReferralCreated }) => {
  const [positions, setPositions] = useState<JobPosition[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState<boolean>(true);

  // Form Fields
  const [candidateName, setCandidateName] = useState<string>('');
  const [candidateEmail, setCandidateEmail] = useState<string>('');
  const [candidatePhone, setCandidatePhone] = useState<string>('');
  const [referredByName, setReferredByName] = useState<string>('');
  const [linkedinUrl, setLinkedinUrl] = useState<string>('');
  const [githubUrl, setGithubUrl] = useState<string>('');
  const [positionId, setPositionId] = useState<string>('');
  const [yearsOfExperience, setYearsOfExperience] = useState<number>(3.0);
  const [relationship, setRelationship] = useState<string>('Former Colleague');
  const [referralNote, setReferralNote] = useState<string>('');
  const [candidateConsent, setCandidateConsent] = useState<boolean>(false);

  // CV File
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Submission State
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successReferralNumber, setSuccessReferralNumber] = useState<string | null>(null);

  // Duplicate Check
  const [duplicateMatches, setDuplicateMatches] = useState<DuplicateMatch[]>([]);
  const [showDuplicateModal, setShowDuplicateModal] = useState<boolean>(false);
  const [duplicateConfirmed, setDuplicateConfirmed] = useState<boolean>(false);

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const jobs = await api.getJobs(false);
        setPositions(jobs);
        if (jobs.length > 0) {
          setPositionId(jobs[0].id);
        }
      } catch (err) {
        console.error('Failed to load job positions:', err);
      } finally {
        setIsLoadingJobs(false);
      }
    };
    fetchPositions();
  }, []);

  const handleFileChange = (file: File | null) => {
    if (!file) return;

    // Validate extension
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.pdf', '.docx'].includes(ext)) {
      setErrorMessage('Invalid file format. Please upload a PDF (.pdf) or Word document (.docx).');
      return;
    }

    // Validate size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage('File exceeds the 10 MB maximum upload limit.');
      return;
    }

    setErrorMessage(null);
    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const performDuplicateCheck = async () => {
    if (!candidateEmail || !candidateName || !candidatePhone || !positionId) return;

    try {
      const res = await api.checkDuplicate({
        candidate_email: candidateEmail,
        candidate_phone: candidatePhone,
        candidate_name: candidateName,
        position_id: positionId,
      });

      if (res.is_duplicate && res.matches.length > 0 && !duplicateConfirmed) {
        setDuplicateMatches(res.matches);
        setShowDuplicateModal(true);
        return true;
      }
    } catch (err) {
      console.warn('Duplicate pre-check error:', err);
    }
    return false;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!referredByName.trim()) {
      setErrorMessage('Please specify who this candidate is referred by.');
      return;
    }

    if (!selectedFile) {
      setErrorMessage('Please upload the candidate’s CV document.');
      return;
    }

    if (!candidateConsent) {
      setErrorMessage('You must confirm that the candidate has agreed to be referred.');
      return;
    }

    // Check duplicate unless already confirmed
    if (!duplicateConfirmed) {
      const isDup = await performDuplicateCheck();
      if (isDup) return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('candidate_name', candidateName);
      formData.append('candidate_email', candidateEmail);
      formData.append('candidate_phone', candidatePhone);
      formData.append('referred_by_name', referredByName.trim());
      formData.append('referred_by', referredByName.trim());
      if (linkedinUrl) formData.append('linkedin_url', linkedinUrl);
      if (githubUrl) formData.append('github_url', githubUrl);
      formData.append('position_id', positionId);
      formData.append('years_of_experience', yearsOfExperience.toString());
      formData.append('relationship', relationship);
      formData.append('referral_note', referralNote);
      formData.append('candidate_consent', 'true');
      formData.append('file', selectedFile);

      const result = await api.submitReferral(formData);
      setSuccessReferralNumber(result.referral_number);
    } catch (err: any) {
      setErrorMessage(
        err.message || 'Referral submission could not be completed. The CV could not be uploaded to SharePoint.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (successReferralNumber) {
    return (
      <div
        className="card card-glass fade-in"
        style={{ maxWidth: '640px', margin: '40px auto', textAlign: 'center', padding: '48px 36px' }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px auto',
          }}
        >
          <CheckCircle2 size={36} color="#10b981" />
        </div>

        <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff', marginBottom: '8px' }}>
          Referral Submitted Successfully!
        </h3>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '20px', lineHeight: 1.5 }}>
          The CV has been safely encrypted and uploaded to the corporate <strong>Microsoft SharePoint document library</strong>, and our HR team has been notified.
        </p>

        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '16px',
            marginBottom: '28px',
            fontFamily: 'var(--font-mono)',
            fontSize: '1.1rem',
            color: '#60a5fa',
            fontWeight: 700,
          }}
        >
          Referral ID: {successReferralNumber}
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setSuccessReferralNumber(null);
              setCandidateName('');
              setCandidateEmail('');
              setCandidatePhone('');
              setLinkedinUrl('');
              setGithubUrl('');
              setReferralNote('');
              setSelectedFile(null);
              setDuplicateConfirmed(false);
            }}
          >
            Submit Another Candidate
          </button>

          <button className="btn btn-primary" onClick={onReferralCreated}>
            View My Referrals
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in" style={{ maxWidth: '840px', margin: '0 auto' }}>
      <div className="card">
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Candidate Referral Submission
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            All resumes are uploaded directly to the corporate Microsoft SharePoint repository via Microsoft Graph API.
          </p>
        </div>

        {errorMessage && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '14px 18px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              fontSize: '0.88rem',
              marginBottom: '24px',
            }}
          >
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Section 1: Candidate Basic Information */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              1. Candidate Information
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">
                  Candidate Full Name <span className="required">*</span>
                </label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Rahul Sharma"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  onBlur={performDuplicateCheck}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  Candidate Email Address <span className="required">*</span>
                </label>
                <input
                  type="email"
                  required
                  className="form-input"
                  placeholder="e.g. rahul.sharma@example.com"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  onBlur={performDuplicateCheck}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">
                  Candidate Phone Number <span className="required">*</span>
                </label>
                <input
                  type="tel"
                  required
                  className="form-input"
                  placeholder="e.g. +1 416-555-0192"
                  value={candidatePhone}
                  onChange={(e) => setCandidatePhone(e.target.value)}
                  onBlur={performDuplicateCheck}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  Years of Relevant Experience <span className="required">*</span>
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="40"
                  required
                  className="form-input"
                  value={yearsOfExperience}
                  onChange={(e) => setYearsOfExperience(parseFloat(e.target.value) || 0)}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">LinkedIn Profile URL</label>
                <input
                  type="url"
                  className="form-input"
                  placeholder="https://linkedin.com/in/candidate"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">GitHub or Portfolio URL</label>
                <input
                  type="url"
                  className="form-input"
                  placeholder="https://github.com/candidate"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginTop: '16px' }}>
              <label className="form-label">
                Referred By <span className="required">*</span>
              </label>
              <input
                type="text"
                required
                className="form-input"
                placeholder="e.g. Employee Full Name (e.g. Rahul Sharma)"
                value={referredByName}
                onChange={(e) => setReferredByName(e.target.value)}
              />
            </div>
          </div>

          {/* Section 2: Job Opening & Relationship */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              2. Position & Referral Context
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">
                  Target Job Position <span className="required">*</span>
                </label>
                {isLoadingJobs ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading positions...</div>
                ) : (
                  <select
                    className="form-select"
                    required
                    value={positionId}
                    onChange={(e) => {
                      setPositionId(e.target.value);
                      performDuplicateCheck();
                    }}
                  >
                    {positions.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title} ({p.department} - {p.location})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">
                  Your Relationship to Candidate <span className="required">*</span>
                </label>
                <select
                  className="form-select"
                  value={relationship}
                  onChange={(e) => setRelationship(e.target.value)}
                >
                  <option value="Former Colleague">Former Colleague</option>
                  <option value="College Alumni">College Alumni</option>
                  <option value="Personal Friend">Personal Friend</option>
                  <option value="Professional Network">Professional Network</option>
                  <option value="Met at Conference / Meetup">Met at Conference / Meetup</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                Referral Recommendation Note <span className="required">*</span>
              </label>
              <textarea
                required
                className="form-textarea"
                rows={4}
                placeholder="Share why you believe this candidate is a great fit for Tangentia. Highlight their key technical strengths, work ethic, and past accomplishments..."
                value={referralNote}
                onChange={(e) => setReferralNote(e.target.value)}
              />
              <span className="form-hint">
                Min. 10 characters. This note is shared directly with the hiring committee.
              </span>
            </div>
          </div>

          {/* Section 3: CV Upload */}
          <div style={{ marginBottom: '28px' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              3. Candidate CV / Resume Upload
            </h4>

            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".pdf,.docx"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />

            {!selectedFile ? (
              <div
                className={`upload-dropzone ${isDragOver ? 'active' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadCloud size={38} color="#3b82f6" />
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Click to browse or drag and drop candidate CV
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Supported formats: PDF (.pdf) or Word (.docx) • Max size: 10 MB
                  </div>
                </div>
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 20px',
                  background: 'var(--bg-secondary)',
                  borderRadius: '10px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <FileText size={28} color="#3b82f6" />
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {selectedFile.name}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for SharePoint sync
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => setSelectedFile(null)}
                >
                  <X size={14} /> Remove
                </button>
              </div>
            )}
          </div>

          {/* Section 4: Mandatory Confirmation */}
          <div
            style={{
              padding: '18px 20px',
              borderRadius: '10px',
              background: 'rgba(59, 130, 246, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              marginBottom: '28px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <input
              type="checkbox"
              id="consent-checkbox"
              style={{ width: '18px', height: '18px', marginTop: '2px', cursor: 'pointer' }}
              checked={candidateConsent}
              onChange={(e) => setCandidateConsent(e.target.checked)}
              required
            />
            <label
              htmlFor="consent-checkbox"
              style={{ fontSize: '0.88rem', color: 'var(--text-primary)', cursor: 'pointer', lineHeight: 1.5 }}
            >
              <strong>Candidate Consent Confirmation:</strong> I confirm that the candidate has explicitly agreed to be referred for employment at Tangentia and consented to their CV being stored in our company SharePoint document repository.
            </label>
          </div>

          {/* Action Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '14px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onReferralCreated()}
              disabled={isSubmitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ padding: '11px 28px' }}
              disabled={isSubmitting || !candidateConsent || !selectedFile}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Uploading CV to SharePoint...
                </>
              ) : (
                <>
                  <UploadCloud size={18} />
                  Submit Referral & Upload CV
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Duplicate Candidate Modal */}
      <DuplicateModal
        isOpen={showDuplicateModal}
        onClose={() => setShowDuplicateModal(false)}
        matches={duplicateMatches}
        candidateName={candidateName}
        onConfirmSubmit={() => {
          setDuplicateConfirmed(true);
          setShowDuplicateModal(false);
        }}
      />
    </div>
  );
};
