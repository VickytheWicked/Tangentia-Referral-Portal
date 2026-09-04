import React, { useEffect, useState } from 'react';
import { ReferralSummary, ReferralDetail, ReferralStatusType } from '../../types';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import { WithdrawModal } from '../../components/employee/WithdrawModal';
import { StatusHistoryTimeline } from '../../components/hr/StatusHistoryTimeline';
import {
  Search,
  Filter,
  Download,
  ExternalLink,
  PlusCircle,
  FileText,
  AlertCircle,
  RotateCcw,
} from 'lucide-react';

interface MyReferralsPageProps {
  onNavigate: (tab: string) => void;
}

export const MyReferralsPage: React.FC<MyReferralsPageProps> = ({ onNavigate }) => {
  const [referrals, setReferrals] = useState<ReferralSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedReferral, setSelectedReferral] = useState<ReferralDetail | null>(null);
  const [withdrawingReferral, setWithdrawingReferral] = useState<{
    id: string;
    candidateName: string;
    referralNumber?: string;
  } | null>(null);

  const fetchReferrals = async () => {
    setIsLoading(true);
    try {
      const data = await api.getMyReferrals();
      setReferrals(data);
    } catch (err) {
      console.error('Failed to load referrals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReferrals();
  }, []);

  const openDetail = async (id: string) => {
    try {
      const detail = await api.getReferralDetail(id);
      setSelectedReferral(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch referral details');
    }
  };

  const handleDownloadCV = async (refId: string, filename: string) => {
    try {
      await api.downloadCV(refId, filename);
    } catch (err: any) {
      alert(err.message || 'Failed to download CV');
    }
  };

  const filtered = referrals.filter((r) => {
    const matchesSearch =
      r.candidate_name.toLowerCase().includes(search.toLowerCase()) ||
      r.candidate_email.toLowerCase().includes(search.toLowerCase()) ||
      r.referral_number.toLowerCase().includes(search.toLowerCase()) ||
      r.position_title.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '24px',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Candidate Referrals
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Manage and track candidate referrals recommended across Tangentia
            </p>
          </div>

          <button className="btn btn-primary btn-sm" onClick={() => onNavigate('submit-referral')}>
            <PlusCircle size={15} /> Submit New Referral
          </button>
        </div>

        {/* Filters Bar */}
        <div style={{ display: 'flex', gap: '14px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
            <Search
              size={16}
              color="var(--text-muted)"
              style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '36px' }}
              placeholder="Filter by candidate, email, ID, or position..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ width: '200px' }}>
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
        </div>

        {/* Table */}
        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading referrals...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center' }}>
            <FileText size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px auto' }} />
            <h4 style={{ color: 'var(--text-secondary)' }}>No matching referrals found</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              Try adjusting your search query or status filter.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Referral ID</th>
                  <th>Candidate</th>
                  <th>Job Opening</th>
                  <th>Referred By</th>
                  <th>Experience</th>
                  <th>Relationship</th>
                  <th>Date Submitted</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
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
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                        {r.referred_by_name || 'N/A'}
                      </div>
                      {r.referred_by_email && (
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                          {r.referred_by_email}
                        </div>
                      )}
                    </td>
                    <td>{r.years_of_experience} yrs</td>
                    <td>{r.relationship}</td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => openDetail(r.id)}
                          title="View Profile"
                        >
                          <ExternalLink size={14} /> View
                        </button>
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => handleDownloadCV(r.id, r.original_filename)}
                          title="Download CV"
                        >
                          <Download size={14} />
                        </button>
                        {['Submitted', 'Under Review'].includes(r.status) && (
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() =>
                              setWithdrawingReferral({
                                id: r.id,
                                candidateName: r.candidate_name,
                                referralNumber: r.referral_number,
                              })
                            }
                            title="Withdraw Referral"
                          >
                            <RotateCcw size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Referral Profile Modal */}
      {selectedReferral && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedReferral(null)}
          title={`Candidate Details: ${selectedReferral.candidate_name}`}
          maxWidth="720px"
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              {['Submitted', 'Under Review'].includes(selectedReferral.status) && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() =>
                    setWithdrawingReferral({
                      id: selectedReferral.id,
                      candidateName: selectedReferral.candidate_name,
                      referralNumber: selectedReferral.referral_number,
                    })
                  }
                >
                  Withdraw Referral
                </button>
              )}
              <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleDownloadCV(selectedReferral.id, selectedReferral.original_filename)}
                >
                  <Download size={14} /> Download CV Document
                </button>
                <button className="btn btn-primary btn-sm" onClick={() => setSelectedReferral(null)}>
                  Close
                </button>
              </div>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px',
                background: 'var(--bg-secondary)',
                borderRadius: '10px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {selectedReferral.referral_number}
                </span>
                <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedReferral.candidate_name}
                </h4>
                <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  {selectedReferral.position_title} • {selectedReferral.position_department}
                </div>
              </div>
              <StatusBadge status={selectedReferral.status} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.86rem' }}>
              <div><strong>Email:</strong> {selectedReferral.candidate_email}</div>
              <div><strong>Phone:</strong> {selectedReferral.candidate_phone}</div>
              <div><strong>Experience:</strong> {selectedReferral.years_of_experience} years</div>
              <div><strong>Relationship:</strong> {selectedReferral.relationship}</div>
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

            <div>
              <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Your Referral Recommendation:
              </h5>
              <div
                style={{
                  background: 'rgba(15, 19, 29, 0.4)',
                  padding: '14px',
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

            <div>
              <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '12px' }}>
                Candidate Progression History
              </h5>
              <StatusHistoryTimeline history={selectedReferral.status_history} />
            </div>
          </div>
        </Modal>
      )}

      {/* Consistent Themed Withdrawal Modal */}
      {withdrawingReferral && (
        <WithdrawModal
          isOpen={true}
          onClose={() => setWithdrawingReferral(null)}
          referralId={withdrawingReferral.id}
          candidateName={withdrawingReferral.candidateName}
          referralNumber={withdrawingReferral.referralNumber}
          onSuccess={() => {
            setSelectedReferral(null);
            fetchReferrals();
          }}
        />
      )}
    </div>
  );
};
