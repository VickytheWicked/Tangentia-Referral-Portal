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

          <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
            Showing <strong>{filteredReferrals.length}</strong> of <strong>{referrals.length}</strong> referrals
          </span>
        </div>

        {/* Filters Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '20px' }}>
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
                      <div style={{ display: 'flex', gap: '6px' }}>
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
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => setStatusModalRef(selectedReferral)}
              >
                <Edit size={14} /> Change Status ({selectedReferral.status})
              </button>

              <div style={{ display: 'flex', gap: '8px' }}>
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
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
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
    </div>
  );
};
