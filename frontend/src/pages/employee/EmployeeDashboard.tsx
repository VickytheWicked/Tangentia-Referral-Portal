import React, { useEffect, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { ReferralSummary, ReferralDetail } from '../../types';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import { WithdrawModal } from '../../components/employee/WithdrawModal';
import { StatusHistoryTimeline } from '../../components/hr/StatusHistoryTimeline';
import {
  PlusCircle,
  Users,
  Clock,
  Award,
  CheckCircle,
  FileText,
  Download,
  ExternalLink,
  Search,
  AlertCircle,
} from 'lucide-react';

interface EmployeeDashboardProps {
  onNavigate: (tab: string) => void;
}

export const EmployeeDashboard: React.FC<EmployeeDashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [referrals, setReferrals] = useState<ReferralSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [selectedReferral, setSelectedReferral] = useState<ReferralDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
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

  const openDetail = async (refSummary: ReferralSummary) => {
    setIsDetailLoading(true);
    try {
      const detail = await api.getReferralDetail(refSummary.id);
      setSelectedReferral(detail);
    } catch (err) {
      console.error('Failed to get referral details:', err);
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleDownloadCV = async (refId: string, filename: string) => {
    try {
      await api.downloadCV(refId, filename);
    } catch (err: any) {
      alert(err.message || 'Failed to download CV');
    }
  };

  // Metrics
  const total = referrals.length;
  const inReview = referrals.filter((r) => ['Submitted', 'Under Review'].includes(r.status)).length;
  const inInterview = referrals.filter((r) => ['Shortlisted', 'Interview', 'Selected'].includes(r.status)).length;
  const hired = referrals.filter((r) => r.status === 'Hired').length;

  const filteredReferrals = referrals.filter(
    (r) =>
      r.candidate_name.toLowerCase().includes(search.toLowerCase()) ||
      r.position_title.toLowerCase().includes(search.toLowerCase()) ||
      r.referral_number.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Welcome Banner */}
      <div
        className="card card-glass"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '28px 32px',
          background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.25) 0%, rgba(15, 23, 42, 0.6) 100%)',
          borderColor: 'rgba(59, 130, 246, 0.25)',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginBottom: '6px' }}>
            Welcome back, {user?.name || 'Employee'}! 👋
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '600px' }}>
            Help shape Tangentia's future by referring exceptional talent. Submit your candidate's CV directly to our SharePoint document repository and track their progress live.
          </p>
        </div>
        <button
          className="btn btn-primary"
          style={{ padding: '12px 24px', fontSize: '0.95rem' }}
          onClick={() => onNavigate('submit-referral')}
        >
          <PlusCircle size={18} />
          Submit New Referral
        </button>
      </div>

      {/* Metrics Row */}
      <div className="metric-grid">
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">My Total Referrals</span>
            <Users size={20} color="#3b82f6" />
          </div>
          <span className="metric-value">{total}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Under Review</span>
            <Clock size={20} color="#f59e0b" />
          </div>
          <span className="metric-value">{inReview}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">In Interview Stages</span>
            <Award size={20} color="#ec4899" />
          </div>
          <span className="metric-value">{inInterview}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Successfully Hired</span>
            <CheckCircle size={20} color="#10b981" />
          </div>
          <span className="metric-value">{hired}</span>
        </div>
      </div>

      {/* Recent Referrals Table */}
      <div className="card">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '20px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              My Submitted Referrals
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Candidates you have recommended to open positions
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ position: 'relative', width: '260px' }}>
              <Search
                size={16}
                color="var(--text-muted)"
                style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
              />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '36px' }}
                placeholder="Search candidate or position..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>

        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading your referrals...
          </div>
        ) : filteredReferrals.length === 0 ? (
          <div style={{ padding: '48px 20px', textAlign: 'center' }}>
            <FileText size={40} color="var(--text-muted)" style={{ margin: '0 auto 12px auto' }} />
            <h4 style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>No referrals found</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '18px' }}>
              You haven't submitted any candidate referrals matching this criteria yet.
            </p>
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate('submit-referral')}>
              <PlusCircle size={14} /> Submit Your First Referral
            </button>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Referral ID</th>
                  <th>Candidate</th>
                  <th>Position</th>
                  <th>Experience</th>
                  <th>Submitted Date</th>
                  <th>Status</th>
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
                    <td>{r.years_of_experience} yrs</td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => openDetail(r)}
                          title="View Details"
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
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Referral Detail Modal */}
      {selectedReferral && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedReferral(null)}
          title={`Candidate Profile: ${selectedReferral.candidate_name}`}
          maxWidth="700px"
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              {['Submitted', 'Under Review'].includes(selectedReferral.status) ? (
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
              ) : (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  In process ({selectedReferral.status})
                </span>
              )}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleDownloadCV(selectedReferral.id, selectedReferral.original_filename)}
                >
                  <Download size={14} /> Download CV Document
                </button>
                <button className="btn btn-primary btn-sm" onClick={() => setSelectedReferral(null)}>
                  Done
                </button>
              </div>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Candidate Header Summary */}
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

            {/* Candidate Details Grid */}
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

            {/* Referral Note */}
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

            {/* Status History Timeline */}
            <div>
              <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '12px' }}>
                Referral Progress Timeline
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
