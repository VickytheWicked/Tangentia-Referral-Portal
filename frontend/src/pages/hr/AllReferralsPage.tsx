import React, { useEffect, useState } from 'react';
import { ReferralSummary, ReferralDetail, JobPosition, ReferralStatusType } from '../../types';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import { StatusChangeModal } from '../../components/hr/StatusChangeModal';
import { HRNotesSection } from '../../components/hr/HRNotesSection';
import { StatusHistoryTimeline } from '../../components/hr/StatusHistoryTimeline';
import {
  Search,
  Filter,
  Download,
  ExternalLink,
  Edit,
  FileText,
  Building,
  Briefcase,
  User,
  Calendar,
  CheckCircle2,
  FileSpreadsheet,
  Archive,
  Trash2,
} from 'lucide-react';

interface AllReferralsPageProps {
  initialSelectedId?: string | null;
  onClearInitialId?: () => void;
}

export const AllReferralsPage: React.FC<AllReferralsPageProps> = ({
  initialSelectedId,
  onClearInitialId,
}) => {
  const [referrals, setReferrals] = useState<ReferralSummary[]>([]);
  const [positions, setPositions] = useState<JobPosition[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Filters
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');
  const [positionFilter, setPositionFilter] = useState<string>('ALL');

  // Candidate Profile Detail Modal
  const [selectedReferral, setSelectedReferral] = useState<ReferralDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);

  // Status Change Modal
  const [statusModalRef, setStatusModalRef] = useState<ReferralSummary | null>(null);

  // Delete Confirmation Modal
  const [deletingReferral, setDeletingReferral] = useState<{ id: string; name: string; number: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Archive Confirmation Modal
  const [archivingReferral, setArchivingReferral] = useState<{
    id: string;
    name: string;
    number: string;
    currentStatus: string;
  } | null>(null);
  const [archiveComment, setArchiveComment] = useState<string>('');
  const [isArchiving, setIsArchiving] = useState<boolean>(false);

  // Excel Export State
  const [isExporting, setIsExporting] = useState<boolean>(false);

  const handleExportExcel = async () => {
    try {
      setIsExporting(true);
      await api.downloadExcelExport();
    } catch (err: any) {
      alert(err.message || 'Failed to export Microsoft Excel workbook.');
    } finally {
      setIsExporting(false);
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [refData, jobsData] = await Promise.all([
        api.getAllReferrals(),
        api.getJobs(true),
      ]);
      setReferrals(refData);
      setPositions(jobsData);
    } catch (err) {
      console.error('Failed to load referrals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCandidateDetail = async (id: string) => {
    setIsDetailLoading(true);
    try {
      const detail = await api.getReferralDetail(id);
      setSelectedReferral(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch candidate details');
    } finally {
      setIsDetailLoading(false);
    }
  };

  useEffect(() => {
    if (initialSelectedId) {
      openCandidateDetail(initialSelectedId);
      if (onClearInitialId) onClearInitialId();
    }
  }, [initialSelectedId]);

  const handleDownloadCV = async (refId: string, filename: string) => {
    try {
      await api.downloadCV(refId, filename);
    } catch (err: any) {
      alert(err.message || 'Failed to download CV');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingReferral) return;
    setIsDeleting(true);
    try {
      await api.deleteReferral(deletingReferral.id);
      setReferrals((prev) => prev.filter((r) => r.id !== deletingReferral.id));
      if (selectedReferral && selectedReferral.id === deletingReferral.id) {
        setSelectedReferral(null);
      }
      setDeletingReferral(null);
    } catch (err: any) {
      alert(err.message || 'Failed to delete referral');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleConfirmArchive = async () => {
    if (!archivingReferral) return;
    setIsArchiving(true);
    try {
      const updated = await api.archiveReferral(
        archivingReferral.id,
        archiveComment || `Archived record (${archivingReferral.currentStatus})`
      );
      setReferrals((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      if (selectedReferral && selectedReferral.id === archivingReferral.id) {
        setSelectedReferral((prev) => (prev ? { ...prev, status: updated.status } : null));
      }
      setArchivingReferral(null);
      setArchiveComment('');
    } catch (err: any) {
      alert(err.message || 'Failed to archive referral');
    } finally {
      setIsArchiving(false);
    }
  };

  // Distinct departments
  const departments = Array.from(new Set(positions.map((p) => p.department))).filter(Boolean);

  const filteredReferrals = referrals.filter((r) => {
    const matchesSearch =
      r.candidate_name.toLowerCase().includes(search.toLowerCase()) ||
      r.candidate_email.toLowerCase().includes(search.toLowerCase()) ||
      r.referral_number.toLowerCase().includes(search.toLowerCase()) ||
      r.referred_by_name.toLowerCase().includes(search.toLowerCase()) ||
      r.position_title.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    const matchesDepartment = departmentFilter === 'ALL' || r.position_department === departmentFilter;
    const matchesPosition = positionFilter === 'ALL' || r.position_id === positionFilter;

    return matchesSearch && matchesStatus && matchesDepartment && matchesPosition;
  });

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Candidate Referrals Database
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Enterprise repository of all candidate submissions with SharePoint CV storage
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleExportExcel}
              disabled={isExporting}
              title="Download Microsoft Excel Online Workbook (.xlsx)"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <FileSpreadsheet size={15} color="#10b981" />
              <span>{isExporting ? 'Exporting...' : 'Export to Excel'}</span>
            </button>

            <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Showing <strong>{filteredReferrals.length}</strong> of <strong>{referrals.length}</strong> referrals
            </span>
          </div>
        </div>

        {/* Filters Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 180px), 1fr))', gap: '12px', marginBottom: '20px' }}>
          <div style={{ position: 'relative' }}>
            <Search
              size={16}
              color="var(--text-muted)"
              style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '36px' }}
              placeholder="Search candidate, referrer, ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div>
            <select
              className="form-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Statuses</option>
              <option value="Submitted">Submitted</option>
              <option value="Under Review">Under Review</option>
              <option value="Shortlisted">Shortlisted</option>
              <option value="Interview">Interview</option>
              <option value="Selected">Selected</option>
              <option value="Hired">Hired</option>
              <option value="Rejected">Rejected</option>
              <option value="Withdrawn">Withdrawn</option>
              <option value="Archived">Archived</option>
            </select>
          </div>

          <div>
            <select
              className="form-select"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
            >
              <option value="ALL">All Departments</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div>
            <select
              className="form-select"
              value={positionFilter}
              onChange={(e) => setPositionFilter(e.target.value)}
            >
              <option value="ALL">All Job Openings</option>
              {positions.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Data Grid */}
        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading candidate database...
          </div>
        ) : filteredReferrals.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No candidate referrals match your search filters.
          </div>
        ) : (
          <>
            <div className="table-scroll-hint">
              <span>⇄ Swipe horizontally to view full candidate database</span>
            </div>
            <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Referral ID</th>
                  <th>Candidate</th>
                  <th>Opening & Department</th>
                  <th>Referred By</th>
                  <th>Submitted</th>
                  <th>Status</th>
                  <th>CV File</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredReferrals.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#93c5fd' }}>
                        {r.referral_number}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{r.candidate_name}</div>
                      <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{r.candidate_email}</div>
                    </td>
                    <td>
                      <div style={{ color: 'var(--text-secondary)' }}>{r.position_title}</div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{r.position_department}</div>
                    </td>
                    <td>
                      <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{r.referred_by_name}</div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{r.relationship}</div>
                    </td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                    <td>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => handleDownloadCV(r.id, r.original_filename)}
                        title="Download CV from SharePoint"
                      >
                        <Download size={14} /> CV
                      </button>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => openCandidateDetail(r.id)}
                          title="Open Candidate Profile & HR Notes"
                        >
                          <ExternalLink size={14} /> Profile
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setStatusModalRef(r)}
                          title="Change Status"
                        >
                          <Edit size={14} />
                        </button>
                        {r.status !== 'Archived' && (
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ color: '#94a3b8' }}
                            onClick={() =>
                              setArchivingReferral({
                                id: r.id,
                                name: r.candidate_name,
                                number: r.referral_number,
                                currentStatus: r.status,
                              })
                            }
                            title="Archive Record"
                          >
                            <Archive size={14} />
                          </button>
                        )}
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() =>
                            setDeletingReferral({
                              id: r.id,
                              name: r.candidate_name,
                              number: r.referral_number,
                            })
                          }
                          title="Delete Referral Permanently"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>

      {/* Comprehensive Candidate Profile Modal */}
      {selectedReferral && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedReferral(null)}
          title={`Candidate Profile: ${selectedReferral.candidate_name}`}
          maxWidth="850px"
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => setStatusModalRef(selectedReferral)}
                >
                  <Edit size={14} /> Change Status ({selectedReferral.status})
                </button>
                {selectedReferral.status !== 'Archived' && (
                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ color: '#94a3b8' }}
                    onClick={() =>
                      setArchivingReferral({
                        id: selectedReferral.id,
                        name: selectedReferral.candidate_name,
                        number: selectedReferral.referral_number,
                        currentStatus: selectedReferral.status,
                      })
                    }
                  >
                    <Archive size={14} /> Archive Record
                  </button>
                )}
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() =>
                    setDeletingReferral({
                      id: selectedReferral.id,
                      name: selectedReferral.candidate_name,
                      number: selectedReferral.referral_number,
                    })
                  }
                >
                  <Trash2 size={14} /> Delete Referral
                </button>
              </div>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleDownloadCV(selectedReferral.id, selectedReferral.original_filename)}
                >
                  <Download size={14} /> Download CV ({selectedReferral.original_filename})
                </button>
                <button className="btn btn-outline btn-sm" onClick={() => setSelectedReferral(null)}>
                  Close
                </button>
              </div>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Header summary */}
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
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {selectedReferral.referral_number}
                </div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {selectedReferral.candidate_name}
                </h3>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {selectedReferral.position_title} • {selectedReferral.position_department}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <StatusBadge status={selectedReferral.status} />
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                  Submitted: {new Date(selectedReferral.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>

            {/* Candidate & Referrer Info Grid */}
            <div
              className="responsive-info-grid"
              style={{
                gap: '16px',
                background: 'rgba(15, 19, 29, 0.4)',
                padding: '16px',
                borderRadius: '10px',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.86rem',
              }}
            >
              <div><strong>Email:</strong> {selectedReferral.candidate_email}</div>
              <div><strong>Phone:</strong> {selectedReferral.candidate_phone}</div>
              <div><strong>Experience:</strong> {selectedReferral.years_of_experience} years</div>
              <div>
                <strong>Referred by:</strong> {selectedReferral.referred_by_name} ({selectedReferral.relationship})
              </div>
              <div><strong>Referrer Email:</strong> {selectedReferral.referred_by_email}</div>
              <div>
                <strong>CV Storage:</strong> SharePoint Online ({selectedReferral.original_filename})
              </div>
              {selectedReferral.linkedin_url && (
                <div>
                  <strong>LinkedIn:</strong>{' '}
                  <a href={selectedReferral.linkedin_url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>
                    View Profile
                  </a>
                </div>
              )}
              {selectedReferral.github_url && (
                <div>
                  <strong>GitHub:</strong>{' '}
                  <a href={selectedReferral.github_url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>
                    View Portfolio
                  </a>
                </div>
              )}
            </div>

            {/* Referring Employee Note */}
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
                {selectedReferral.referral_note}
              </div>
            </div>

            {/* HR Confidential Notes Thread */}
            <HRNotesSection
              referralId={selectedReferral.id}
              notes={selectedReferral.hr_notes || []}
              onNoteAdded={() => openCandidateDetail(selectedReferral.id)}
            />

            {/* Status History Timeline */}
            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '12px' }}>
                Status Transition Audit Trail
              </h4>
              <StatusHistoryTimeline history={selectedReferral.status_history || []} />
            </div>
          </div>
        </Modal>
      )}

      {/* Status Update Modal */}
      {statusModalRef && (
        <StatusChangeModal
          isOpen={true}
          onClose={() => setStatusModalRef(null)}
          referralId={statusModalRef.id}
          candidateName={statusModalRef.candidate_name}
          currentStatus={statusModalRef.status}
          onStatusUpdated={() => {
            loadData();
            if (selectedReferral && selectedReferral.id === statusModalRef.id) {
              openCandidateDetail(statusModalRef.id);
            }
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deletingReferral && (
        <Modal
          isOpen={true}
          onClose={() => !isDeleting && setDeletingReferral(null)}
          title="Delete Referral Permanently"
          maxWidth="520px"
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setDeletingReferral(null)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger btn-sm"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Permanently Delete'}
              </button>
            </div>
          }
        >
          <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', padding: '6px 0' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '50%',
                background: 'rgba(239, 68, 68, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Trash2 size={22} color="#ef4444" />
            </div>
            <div>
              <h4 style={{ color: 'var(--text-primary)', marginBottom: '8px', fontSize: '1.05rem' }}>
                Delete {deletingReferral.name}?
              </h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: '1.5', marginBottom: '12px' }}>
                Are you sure you want to permanently delete referral <strong style={{ fontFamily: 'var(--font-mono)' }}>{deletingReferral.number}</strong> for <strong>{deletingReferral.name}</strong>?
              </p>
              <p style={{ color: '#f87171', fontSize: '0.82rem', lineHeight: '1.4', background: 'rgba(239, 68, 68, 0.08)', padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                ⚠️ <strong>Warning:</strong> This will delete candidate information, all internal confidential HR notes, status history audit logs, and remove the record from Microsoft Excel. This action cannot be undone.
              </p>
            </div>
          </div>
        </Modal>
      )}

      {/* Archive Confirmation Modal */}
      {archivingReferral && (
        <Modal
          isOpen={true}
          onClose={() => !isArchiving && setArchivingReferral(null)}
          title="Archive Candidate Referral"
          maxWidth="520px"
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setArchivingReferral(null)}
                disabled={isArchiving}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleConfirmArchive}
                disabled={isArchiving}
              >
                {isArchiving ? 'Archiving...' : 'Archive Record'}
              </button>
            </div>
          }
        >
          <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', padding: '6px 0' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '50%',
                background: 'rgba(148, 163, 184, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Archive size={22} color="#94a3b8" />
            </div>
            <div style={{ flex: 1 }}>
              <h4 style={{ color: 'var(--text-primary)', marginBottom: '8px', fontSize: '1.05rem' }}>
                Archive {archivingReferral.name}
              </h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: '1.5', marginBottom: '14px' }}>
                Current Status: <strong>{archivingReferral.currentStatus}</strong>. Archiving preserves this candidate referral as an inactive historical record (even if previously rejected or withdrawn).
              </p>
              <div className="form-group">
                <label className="form-label">Archive Note / Reason (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Preserving record for future talent pool matching..."
                  value={archiveComment}
                  onChange={(e) => setArchiveComment(e.target.value)}
                />
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
