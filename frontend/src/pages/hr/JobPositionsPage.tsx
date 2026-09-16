import React, { useEffect, useState } from 'react';
import { JobPosition } from '../../types';
import { api } from '../../services/api';
import { Modal } from '../../components/common/Modal';
import {
  Briefcase,
  Plus,
  MapPin,
  Clock,
  Edit2,
  CheckCircle2,
  XCircle,
  Building,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';

export const JobPositionsPage: React.FC = () => {
  const [positions, setPositions] = useState<JobPosition[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [includeInactive, setIncludeInactive] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [deactivateOnSync, setDeactivateOnSync] = useState<boolean>(false);
  const [syncFeedback, setSyncFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingJob, setEditingJob] = useState<JobPosition | null>(null);

  // Form Fields
  const [title, setTitle] = useState<string>('');
  const [department, setDepartment] = useState<string>('Engineering');
  const [description, setDescription] = useState<string>('');
  const [location, setLocation] = useState<string>('Toronto, Canada (Hybrid)');
  const [employmentType, setEmploymentType] = useState<string>('Full-time');
  const [isActive, setIsActive] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchJobs = async () => {
    setIsLoading(true);
    try {
      const data = await api.getJobs(includeInactive);
      setPositions(data);
    } catch (err) {
      console.error('Failed to load jobs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [includeInactive]);

  const handleSyncCats = async () => {
    setIsSyncing(true);
    setSyncFeedback(null);
    try {
      const res = await api.syncCatsJobs(deactivateOnSync);
      const deactivatedPart = deactivateOnSync && res.deactivated_count > 0
        ? `, ${res.deactivated_count} deactivated`
        : '';
      setSyncFeedback({
        type: 'success',
        message: `Successfully synchronized ${res.total_scraped} openings from Tangentia CATS Careers! (${res.created_count} added, ${res.updated_count} updated${deactivatedPart})`,
      });
      await fetchJobs();
      setTimeout(() => setSyncFeedback(null), 8000);
    } catch (err: any) {
      setSyncFeedback({
        type: 'error',
        message: err.message || 'Failed to synchronize openings from Tangentia CATS Careers.',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const openCreateModal = () => {
    setEditingJob(null);
    setTitle('');
    setDepartment('Engineering');
    setDescription('');
    setLocation('Toronto, Canada (Hybrid)');
    setEmploymentType('Full-time');
    setIsActive(true);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (job: JobPosition) => {
    setEditingJob(job);
    setTitle(job.title);
    setDepartment(job.department);
    setDescription(job.description);
    setLocation(job.location);
    setEmploymentType(job.employment_type);
    setIsActive(job.is_active);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    try {
      if (editingJob) {
        await api.updateJob(editingJob.id, {
          title,
          department,
          description,
          location,
          employment_type: employmentType,
          is_active: isActive,
        });
      } else {
        await api.createJob({
          title,
          department,
          description,
          location,
          employment_type: employmentType,
          is_active: isActive,
        });
      }
      setIsModalOpen(false);
      fetchJobs();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save job position');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleJobStatus = async (job: JobPosition) => {
    try {
      await api.updateJob(job.id, { is_active: !job.is_active });
      fetchJobs();
    } catch (err: any) {
      alert(err.message || 'Failed to toggle job status');
    }
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Open Job Positions
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Manage corporate job requisitions available for employee referrals
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.84rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
              />
              Show archived positions
            </label>

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleSyncCats}
                disabled={isSyncing}
                title="Scrape and synchronize live open requisitions from Tangentia CATS Careers"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <RefreshCw size={15} className={isSyncing ? 'spin' : ''} />
                {isSyncing ? 'Syncing CATS...' : 'Sync CATS ATS'}
              </button>
              <label
                title="When enabled, CATS-imported positions that no longer appear on the CATS portal will be automatically archived after syncing."
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  fontSize: '0.75rem',
                  color: deactivateOnSync ? '#f59e0b' : 'var(--text-muted)',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <input
                  type="checkbox"
                  checked={deactivateOnSync}
                  onChange={(e) => setDeactivateOnSync(e.target.checked)}
                  style={{ width: '12px', height: '12px', accentColor: '#f59e0b' }}
                />
                Auto-archive removed
              </label>
            </div>

            <button className="btn btn-primary btn-sm" onClick={openCreateModal}>
              <Plus size={16} /> Add New Opening
            </button>
          </div>
        </div>

        {syncFeedback && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '0.86rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: syncFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: syncFeedback.type === 'success' ? '#34d399' : '#f87171',
              border: `1px solid ${syncFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            }}
          >
            <span>{syncFeedback.message}</span>
            <button
              onClick={() => setSyncFeedback(null)}
              style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer', padding: '2px 6px', fontSize: '0.9rem' }}
            >
              ✕
            </button>
          </div>
        )}

        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading job requisitions...
          </div>
        ) : positions.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No job openings found. Click "Add New Opening" or "Sync CATS ATS" to load requisitions.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: '18px' }}>
            {positions.map((job) => (
              <div
                key={job.id}
                style={{
                  background: 'var(--bg-secondary)',
                  border: `1px solid ${job.is_active ? 'var(--border-subtle)' : 'rgba(239, 68, 68, 0.2)'}`,
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  opacity: job.is_active ? 1 : 0.65,
                  transition: 'transform var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          color: '#60a5fa',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                        }}
                      >
                        {job.department}
                      </span>
                      {job.id.startsWith('cats-') && (
                        <span
                          style={{
                            fontSize: '0.66rem',
                            fontWeight: 700,
                            padding: '1px 6px',
                            borderRadius: '4px',
                            background: 'rgba(59, 130, 246, 0.15)',
                            color: '#93c5fd',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                          }}
                          title="Imported from Tangentia CATS Careers ATS"
                        >
                          CATS ATS
                        </span>
                      )}
                    </div>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {job.title}
                    </h4>
                  </div>

                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: '12px',
                      background: job.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: job.is_active ? '#34d399' : '#f87171',
                      border: `1px solid ${job.is_active ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                    }}
                  >
                    {job.is_active ? 'Active' : 'Archived'}
                  </span>
                </div>

                <p
                  style={{
                    fontSize: '0.84rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.5,
                    flex: 1,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={job.description}
                >
                  {job.description}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={13} /> {job.location}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={13} /> {job.employment_type}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', marginTop: '4px' }}>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => toggleJobStatus(job)}
                  >
                    {job.is_active ? (
                      <>
                        <XCircle size={14} color="#f87171" /> Deactivate
                      </>
                    ) : (
                      <>
                        <CheckCircle2 size={14} color="#34d399" /> Activate
                      </>
                    )}
                  </button>

                  <button className="btn btn-secondary btn-sm" onClick={() => openEditModal(job)}>
                    <Edit2 size={14} /> Edit
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <Modal
          isOpen={true}
          onClose={() => setIsModalOpen(false)}
          title={editingJob ? 'Edit Job Opening' : 'Create New Job Opening'}
          maxWidth="600px"
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={isSubmitting || !title.trim() || !description.trim()}
              >
                {isSubmitting ? 'Saving...' : editingJob ? 'Update Position' : 'Create Position'}
              </button>
            </>
          }
        >
          <form onSubmit={handleSubmit}>
            {formError && (
              <div style={{ color: '#ef4444', marginBottom: '14px', fontSize: '0.86rem' }}>{formError}</div>
            )}

            <div className="form-group">
              <label className="form-label">Job Title <span className="required">*</span></label>
              <input
                type="text"
                required
                className="form-input"
                placeholder="e.g. Senior Backend Developer"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="responsive-form-row">
              <div className="form-group">
                <label className="form-label">Department <span className="required">*</span></label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Engineering, Sales, AI"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Employment Type</label>
                <select
                  className="form-select"
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value)}
                >
                  <option value="Full-time">Full-time</option>
                  <option value="Part-time">Part-time</option>
                  <option value="Contract">Contract</option>
                  <option value="Internship">Internship</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Location <span className="required">*</span></label>
              <input
                type="text"
                required
                className="form-input"
                placeholder="e.g. Toronto, Canada (Hybrid) or Remote"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Role Description (1–2 lines) <span className="required">*</span></label>
              <textarea
                required
                className="form-textarea"
                rows={2}
                placeholder="Brief 1-2 line summary of role qualifications and core responsibilities..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
              <input
                type="checkbox"
                id="is-active-check"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              <label htmlFor="is-active-check" style={{ fontSize: '0.86rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
                Requisition is active and open for employee referrals
              </label>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
