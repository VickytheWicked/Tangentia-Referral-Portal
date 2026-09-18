import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import { JobPosition, DuplicateMatch } from '../../types';
import { api } from '../../services/api';
import { DuplicateModal } from '../../components/common/DuplicateModal';
import { JobUnavailableModal } from '../../components/common/JobUnavailableModal';
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

const COUNTRY_CODES = [
  { code: '+91', label: '+91 (India)', country: 'India' },
  { code: '+1', label: '+1 (Canada / US)', country: 'Canada/US' },
  { code: '+44', label: '+44 (UK)', country: 'UK' },
  { code: '+971', label: '+971 (UAE)', country: 'UAE' },
  { code: '+61', label: '+61 (Australia)', country: 'Australia' },
  { code: '+65', label: '+65 (Singapore)', country: 'Singapore' },
  { code: '+49', label: '+49 (Germany)', country: 'Germany' },
  { code: '+33', label: '+33 (France)', country: 'France' },
  { code: '+81', label: '+81 (Japan)', country: 'Japan' },
  { code: '+86', label: '+86 (China)', country: 'China' },
  { code: '+52', label: '+52 (Mexico)', country: 'Mexico' },
  { code: '+55', label: '+55 (Brazil)', country: 'Brazil' },
  { code: '+27', label: '+27 (South Africa)', country: 'South Africa' },
  { code: '+353', label: '+353 (Ireland)', country: 'Ireland' },
  { code: '+31', label: '+31 (Netherlands)', country: 'Netherlands' },
  { code: '+41', label: '+41 (Switzerland)', country: 'Switzerland' },
  { code: '+64', label: '+64 (New Zealand)', country: 'New Zealand' },
  { code: '+63', label: '+63 (Philippines)', country: 'Philippines' },
  { code: '+92', label: '+92 (Pakistan)', country: 'Pakistan' },
  { code: '+880', label: '+880 (Bangladesh)', country: 'Bangladesh' },
  { code: '+94', label: '+94 (Sri Lanka)', country: 'Sri Lanka' },
];

interface SubmitReferralPageProps {
  onReferralCreated: () => void;
}

export const SubmitReferralPage: React.FC<SubmitReferralPageProps> = ({ onReferralCreated }) => {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const preselectedJobId =
    searchParams.get('positionId') ||
    searchParams.get('jobId') ||
    (location.state as any)?.positionId ||
    (location.state as any)?.jobId ||
    '';

  const [positions, setPositions] = useState<JobPosition[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState<boolean>(true);

  // Form Fields
  // Employee Information
  const [employeeName, setEmployeeName] = useState<string>('');
  const [employeeEmail, setEmployeeEmail] = useState<string>('');
  const [employeeCountryCode, setEmployeeCountryCode] = useState<string>('+91');
  const [employeePhone, setEmployeePhone] = useState<string>('');

  // Referral Information
  const [referralName, setReferralName] = useState<string>('');
  const [referralEmail, setReferralEmail] = useState<string>('');
  const [referralCountryCode, setReferralCountryCode] = useState<string>('+91');
  const [referralPhone, setReferralPhone] = useState<string>('');
  const [linkedinUrl, setLinkedinUrl] = useState<string>('');
  const [githubUrl, setGithubUrl] = useState<string>('');
  const [positionId, setPositionId] = useState<string>(preselectedJobId);
  const [yearsOfExperience, setYearsOfExperience] = useState<string>('3');
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

  // Position Unavailable Modal
  const [showUnavailableModal, setShowUnavailableModal] = useState<boolean>(false);
  const [unavailableJobTitle, setUnavailableJobTitle] = useState<string>('');

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const jobs = await api.getJobs(false);
        setPositions(jobs);
        if (jobs.length > 0) {
          if (preselectedJobId && jobs.some((j) => j.id === preselectedJobId)) {
            setPositionId(preselectedJobId);
          } else if (preselectedJobId) {
            // Position was preselected in URL / navigation state, but is no longer in active list
            try {
              const directJob = await api.getJob(preselectedJobId);
              setUnavailableJobTitle(directJob?.title || 'Selected Position');
            } catch {
              setUnavailableJobTitle('Selected Position');
            }
            setShowUnavailableModal(true);
            setPositionId(jobs[0].id);
          } else if (!positionId) {
            setPositionId(jobs[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to load job positions:', err);
      } finally {
        setIsLoadingJobs(false);
      }
    };
    fetchPositions();
  }, [preselectedJobId]);

  const selectedJob = positions.find((p) => p.id === positionId);

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

  const getFullReferralPhone = (rawPhone: string, code: string) => {
    const trimmed = rawPhone.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('+')) return trimmed;
    return `${code} ${trimmed}`;
  };

  const getFullEmployeePhone = (rawPhone: string, code: string) => {
    const trimmed = rawPhone.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('+')) return trimmed;
    return `${code} ${trimmed}`;
  };

  const performDuplicateCheck = async () => {
    const emailToCheck = referralEmail.trim();
    const phoneToCheck = getFullReferralPhone(referralPhone, referralCountryCode);
    const nameToCheck = referralName.trim();

    if (!nameToCheck || !emailToCheck || !positionId) return false;

    try {
      const res = await api.checkDuplicate({
        candidate_email: emailToCheck,
        candidate_phone: phoneToCheck || 'N/A',
        candidate_name: nameToCheck,
        position_id: positionId,
      });

      if (res.is_duplicate && res.matches.length > 0) {
        setDuplicateMatches(res.matches);
        if (!duplicateConfirmed) {
          setShowDuplicateModal(true);
          const matchReasons = res.matches
            .map((m) => `[Referral #${m.referral_number}: ${m.match_reason}]`)
            .join('; ');
          setErrorMessage(
            `Duplicate Referral Warning: Found ${res.matches.length} existing record(s) matching your input. Exact duplicate reason(s): ${matchReasons}. Trimmed values checked — Name: "${nameToCheck}", Email: "${emailToCheck}"${phoneToCheck ? `, Phone: "${phoneToCheck}"` : ''}. Review the modal or click 'Confirm & Proceed with Submission' to override.`
          );
          return true;
        }
      } else {
        setDuplicateMatches([]);
      }
    } catch (err) {
      console.warn('Duplicate pre-check error:', err);
    }
    return false;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmployeeName = employeeName.trim();
    const cleanEmployeeEmail = employeeEmail.trim().toLowerCase();
    const cleanEmployeePhone = getFullEmployeePhone(employeePhone, employeeCountryCode);
    const cleanReferralName = referralName.trim();
    const cleanReferralEmail = referralEmail.trim().toLowerCase();
    const cleanReferralPhone = getFullReferralPhone(referralPhone, referralCountryCode);

    if (!cleanEmployeeName) {
      setErrorMessage('Please enter your Employee Full Name.');
      return;
    }

    if (!cleanEmployeeEmail) {
      setErrorMessage('Please enter your Employee Email Address.');
      return;
    }

    if (!cleanEmployeeEmail.endsWith('@tangentia.com')) {
      setErrorMessage('Access restricted: Employee Email Address must be an official @tangentia.com corporate email.');
      return;
    }

    if (!employeePhone.trim()) {
      setErrorMessage('Please enter your Employee Phone Number.');
      return;
    }

    if (!cleanReferralName) {
      setErrorMessage('Please enter the Name of the Referral.');
      return;
    }

    if (!cleanReferralEmail) {
      setErrorMessage('Please enter the Referral’s Email Address.');
      return;
    }

    if (!referralPhone.trim()) {
      setErrorMessage('Please enter the Referral’s Phone Number.');
      return;
    }

    const numExperience = parseFloat(yearsOfExperience);
    if (isNaN(numExperience) || numExperience < 0 || numExperience > 50) {
      setErrorMessage('Please enter a valid number of years of experience (e.g. 3 or 4.5).');
      return;
    }

    if (!selectedFile) {
      setErrorMessage('Please upload the referral candidate’s CV document.');
      return;
    }

    if (!candidateConsent) {
      setErrorMessage('You must confirm that the referral has agreed to be referred.');
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
      formData.append('candidate_name', cleanReferralName);
      formData.append('candidate_email', cleanReferralEmail);
      formData.append('candidate_phone', cleanReferralPhone);
      formData.append('referred_by_name', cleanEmployeeName);
      formData.append('referred_by', cleanEmployeeName);
      formData.append('referred_by_email', cleanEmployeeEmail);
      formData.append('employee_email', cleanEmployeeEmail);
      formData.append('referred_by_phone', cleanEmployeePhone);
      formData.append('employee_phone', cleanEmployeePhone);
      if (linkedinUrl) formData.append('linkedin_url', linkedinUrl);
      if (githubUrl) formData.append('github_url', githubUrl);
      formData.append('position_id', positionId);
      formData.append('years_of_experience', numExperience.toString());
      formData.append('relationship', relationship);
      formData.append('referral_note', referralNote);
      formData.append('candidate_consent', 'true');
      formData.append('file', selectedFile);

      const result = await api.submitReferral(formData);
      setSuccessReferralNumber(result.referral_number);
    } catch (err: any) {
      if (err.message && (err.message.toLowerCase().includes('no longer open') || err.message.toLowerCase().includes('invalid or no longer open'))) {
        setUnavailableJobTitle(selectedJob?.title || 'Selected Position');
        setShowUnavailableModal(true);
      } else {
        setErrorMessage(
          err.message || 'Referral submission could not be completed. The CV could not be uploaded to SharePoint.'
        );
      }
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

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setSuccessReferralNumber(null);
              setReferralName('');
              setReferralEmail('');
              setReferralPhone('');
              setLinkedinUrl('');
              setGithubUrl('');
              setReferralNote('');
              setSelectedFile(null);
              setDuplicateConfirmed(false);
            }}
          >
            Submit Another Referral
          </button>

          <button className="btn btn-primary" onClick={onReferralCreated}>
            View Referrals
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
            Submit a Referral
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Provide your employee information and the referral's details. Resumes are stored directly in SharePoint and synced to Excel.
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
          {/* Section 1: Employee Information */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              1. Employee Information
            </h4>

            <div className="responsive-form-row">
              <div className="form-group">
                <label className="form-label">
                  Employee Full Name <span className="required">*</span>
                </label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Rahul Sharma"
                  value={employeeName}
                  onChange={(e) => setEmployeeName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  Employee Email Address (@tangentia.com) <span className="required">*</span>
                </label>
                <input
                  type="email"
                  required
                  className="form-input"
                  placeholder="e.g. rahul.sharma@tangentia.com"
                  value={employeeEmail}
                  onChange={(e) => setEmployeeEmail(e.target.value)}
                />
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                  Must be your official <strong style={{ color: '#93c5fd' }}>@tangentia.com</strong> corporate email
                </span>
              </div>
            </div>

            <div className="responsive-form-row">
              <div className="form-group">
                <label className="form-label">
                  Employee Phone Number <span className="required">*</span>
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <select
                    className="form-select"
                    style={{
                      width: '120px',
                      flexShrink: 0,
                      cursor: 'pointer',
                    }}
                    value={employeeCountryCode}
                    onChange={(e) => setEmployeeCountryCode(e.target.value)}
                  >
                    {COUNTRY_CODES.map((c) => (
                      <option key={`emp-${c.code}-${c.country}`} value={c.code}>
                        {c.code} ({c.country})
                      </option>
                    ))}
                  </select>
                  <input
                    type="tel"
                    required
                    className="form-input"
                    style={{ flex: 1 }}
                    placeholder="e.g. 98200 12345 or 416-555-0192"
                    value={employeePhone}
                    onChange={(e) => setEmployeePhone(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Name of the Referral <span className="required">*</span>
                </label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Priya Patel (Candidate being referred)"
                  value={referralName}
                  onChange={(e) => {
                    setReferralName(e.target.value);
                    setDuplicateConfirmed(false);
                    if (errorMessage && errorMessage.includes('Duplicate Referral')) {
                      setErrorMessage(null);
                    }
                  }}
                  onBlur={performDuplicateCheck}
                />
              </div>
            </div>
          </div>

          {/* Section 2: Position & Referral Context */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              2. Position & Referral Context
            </h4>

            {preselectedJobId && selectedJob && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(30, 58, 138, 0.08) 100%)',
                  border: '1px solid rgba(59, 130, 246, 0.35)',
                  borderRadius: '10px',
                  marginBottom: '16px',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Building2 size={20} color="#60a5fa" />
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Fixed Target Opening
                    </span>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
                      {selectedJob.title}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: '6px',
                      background: 'rgba(59, 130, 246, 0.2)',
                      color: '#93c5fd',
                    }}
                  >
                    {selectedJob.department}
                  </span>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {selectedJob.location} • {selectedJob.employment_type}
                  </span>
                </div>
              </div>
            )}

            <div className="responsive-form-row">
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>Target Job Position <span className="required">*</span></span>
                  {preselectedJobId && positions.some((p) => p.id === positionId) && (
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: '#60a5fa',
                        background: 'rgba(59, 130, 246, 0.15)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        padding: '1px 8px',
                        borderRadius: '4px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}
                    >
                      Target Role Fixed
                    </span>
                  )}
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
                      setDuplicateConfirmed(false);
                      if (errorMessage && errorMessage.includes('Duplicate Referral')) {
                        setErrorMessage(null);
                      }
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
                  Your Relationship to Referral <span className="required">*</span>
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

            <div className="responsive-form-row">
              <div className="form-group">
                <label className="form-label">
                  Referral's Email Address <span className="required">*</span>
                </label>
                <input
                  type="email"
                  required
                  className="form-input"
                  placeholder="e.g. priya.patel@example.com"
                  value={referralEmail}
                  onChange={(e) => {
                    setReferralEmail(e.target.value);
                    setDuplicateConfirmed(false);
                    if (errorMessage && errorMessage.includes('Duplicate Referral')) {
                      setErrorMessage(null);
                    }
                  }}
                  onBlur={performDuplicateCheck}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  Referral's Phone Number <span className="required">*</span>
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <select
                    className="form-select"
                    style={{
                      width: '120px',
                      flexShrink: 0,
                      cursor: 'pointer',
                    }}
                    value={referralCountryCode}
                    onChange={(e) => {
                      setReferralCountryCode(e.target.value);
                      setDuplicateConfirmed(false);
                      if (errorMessage && errorMessage.includes('Duplicate Referral')) {
                        setErrorMessage(null);
                      }
                    }}
                  >
                    {COUNTRY_CODES.map((c) => (
                      <option key={`ref-${c.code}-${c.country}`} value={c.code}>
                        {c.code} ({c.country})
                      </option>
                    ))}
                  </select>
                  <input
                    type="tel"
                    required
                    className="form-input"
                    style={{ flex: 1 }}
                    placeholder="e.g. 98200 12345 or 416-555-0199"
                    value={referralPhone}
                    onChange={(e) => {
                      setReferralPhone(e.target.value);
                      setDuplicateConfirmed(false);
                      if (errorMessage && errorMessage.includes('Duplicate Referral')) {
                        setErrorMessage(null);
                      }
                    }}
                    onBlur={performDuplicateCheck}
                  />
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                  Stored in Excel as: {getFullReferralPhone(referralPhone, referralCountryCode) || `${referralCountryCode} [phone]`}
                </span>
              </div>
            </div>

            <div className="responsive-form-row">
              <div className="form-group">
                <label className="form-label">
                  Years of Relevant Experience <span className="required">*</span>
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  pattern="[0-9]*[.]?[0-9]*"
                  required
                  className="form-input"
                  placeholder="e.g. 3 or 4.5"
                  value={yearsOfExperience}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d*\.?\d*$/.test(val)) {
                      setYearsOfExperience(val);
                    }
                  }}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Referral's LinkedIn Profile URL</label>
                <input
                  type="url"
                  className="form-input"
                  placeholder="https://linkedin.com/in/referral"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label">Referral's GitHub or Portfolio URL</label>
              <input
                type="url"
                className="form-input"
                placeholder="https://github.com/referral"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                Referral Recommendation Note <span className="required">*</span>
              </label>
              <textarea
                required
                className="form-textarea"
                rows={4}
                placeholder="Share why you believe this referral is a great fit for Tangentia. Highlight their key technical strengths, work ethic, and past accomplishments..."
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
              3. Referral CV / Resume Upload
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
                    Click to browse or drag and drop referral's CV
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
              <strong>Referral Consent Confirmation:</strong> I confirm that the referral candidate has explicitly agreed to be referred for employment at Tangentia and consented to their CV being stored in our company SharePoint document repository.
            </label>
          </div>

          {/* Action Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '14px', flexWrap: 'wrap' }}>
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
        candidateName={referralName}
        checkedEmail={referralEmail}
        checkedPhone={getFullReferralPhone(referralPhone, referralCountryCode)}
        onConfirmSubmit={() => {
          setDuplicateConfirmed(true);
          setShowDuplicateModal(false);
          setErrorMessage(null);
        }}
      />

      {/* Position Unavailable Notice Modal */}
      <JobUnavailableModal
        isOpen={showUnavailableModal}
        onClose={() => setShowUnavailableModal(false)}
        jobTitle={unavailableJobTitle}
      />
    </div>
  );
};
