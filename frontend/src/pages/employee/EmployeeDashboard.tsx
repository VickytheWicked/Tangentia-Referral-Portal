import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { ReferralSummary, ReferralDetail, JobPosition } from '../../types';
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
  Briefcase,
  MapPin,
  ArrowRight,
} from 'lucide-react';
import { onReferralUpdated } from '../../services/referralEvents';

interface EmployeeDashboardProps {
  onNavigate: (tab: string) => void;
}

let cachedEmployeeReferrals: ReferralSummary[] = [];
let cachedEmployeeOpenings: JobPosition[] = [];

export const EmployeeDashboard: React.FC<EmployeeDashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [referrals, setReferrals] = useState<ReferralSummary[]>(() => cachedEmployeeReferrals);
  const [isLoading, setIsLoading] = useState<boolean>(() => cachedEmployeeReferrals.length === 0);
  const [openings, setOpenings] = useState<JobPosition[]>(() => cachedEmployeeOpenings);
  const [isOpeningsLoading, setIsOpeningsLoading] = useState<boolean>(() => cachedEmployeeOpenings.length === 0);
  const [search, setSearch] = useState<string>('');
  const [selectedReferral, setSelectedReferral] = useState<ReferralDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
  const [withdrawingReferral, setWithdrawingReferral] = useState<{
    id: string;
    candidateName: string;
    referralNumber?: string;
  } | null>(null);

  const fetchReferrals = async (silent = false) => {
    if (!silent && referrals.length === 0 && cachedEmployeeReferrals.length === 0) {
      setIsLoading(true);
    }
    try {
      const data = await api.getMyReferrals();
      if (Array.isArray(data) && (data.length > 0 || !silent || cachedEmployeeReferrals.length === 0)) {
        cachedEmployeeReferrals = data;
        setReferrals(data);
      }
    } catch (err) {
      console.error('Failed to load referrals:', err);
    } finally {
      if (!silent) {
        setIsLoading(false);
      }
    }
  };

  const fetchOpenings = async (silent = false) => {
    if (!silent && openings.length === 0 && cachedEmployeeOpenings.length === 0) {
      setIsOpeningsLoading(true);
    }
    try {
      const data = await api.getJobs(false);
      if (Array.isArray(data) && (data.length > 0 || !silent || cachedEmployeeOpenings.length === 0)) {
        cachedEmployeeOpenings = data;
        setOpenings(data);
      }
    } catch (err) {
      console.error('Failed to load openings:', err);
    } finally {
      if (!silent) {
        setIsOpeningsLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchReferrals();
    fetchOpenings();

    const unsubscribe = onReferralUpdated(() => {
      fetchReferrals(true);
    });

    const timer = setInterval(() => {
      fetchReferrals(true);
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(timer);
    };
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
        className="card card-glass responsive-banner"
        style={{
          padding: '24px 28px',
          background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.25) 0%, rgba(15, 23, 42, 0.6) 100%)',
          borderColor: 'rgba(59, 130, 246, 0.25)',
        }}
      >
        <div>
          <div style={{ marginBottom: '12px' }}>
            <div className="brand-logo-badge-sm" title="Tangentia Referral Portal">
              <img
                src="/Tangentia-Logo-2026-Black-scaled.png"
                alt="Tangentia"
                className="brand-logo-img"
              />
            </div>
          </div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#fff', marginBottom: '6px' }}>
            Welcome back! 👋
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '640px', lineHeight: 1.5 }}>
            Help shape Tangentia's future by referring exceptional talent. Submit your candidate's CV directly to our secure cloud repository and track their progress live.
          </p>
        </div>
        <button
          className="btn btn-primary"
          style={{ padding: '12px 22px', fontSize: '0.92rem', flexShrink: 0 }}
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
            <span className="metric-label">Total Referrals</span>
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

        <div
          className="metric-card"
          style={{ cursor: 'pointer' }}
          onClick={() => onNavigate('hired-history')}
          title="View all hired candidates in Hired History"
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Successfully Hired</span>
            <CheckCircle size={20} color="#10b981" />
          </div>
          <span className="metric-value">{hired}</span>
        </div>
      </div>

      {/* Available Openings Section */}
      <div className="card">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '18px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Briefcase size={20} color="#60a5fa" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Available Openings
              </h3>
              {!isOpeningsLoading && openings.length > 0 && (
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: 'rgba(59, 130, 246, 0.15)',
                    color: '#93c5fd',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                  }}
                >
                  {openings.length} Active {openings.length === 1 ? 'Role' : 'Roles'}
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '3px' }}>
              Explore current open positions. Click any opening to submit a referral with this target job position fixed.
            </p>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={() => onNavigate('openings')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>View All Openings</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {isOpeningsLoading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading available openings...
          </div>
        ) : openings.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Briefcase size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px auto' }} />
            <p style={{ fontSize: '0.88rem' }}>No open job positions currently available.</p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))',
              gap: '16px',
            }}
          >
            {openings.slice(0, 4).map((job) => (
              <div
                key={job.id}
                onClick={() => {
                  navigate(`/employee/submit?positionId=${encodeURIComponent(job.id)}`, {
                    state: { positionId: job.id },
                  });
                }}
                className="hover-card"
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        color: '#60a5fa',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}
                    >
                      {job.department}
                    </span>
                    {job.id.startsWith('cats-') && (
                      <span
                        style={{
                          fontSize: '0.64rem',
                          fontWeight: 700,
                          padding: '1px 5px',
                          borderRadius: '4px',
                          background: 'rgba(59, 130, 246, 0.15)',
                          color: '#93c5fd',
                          border: '1px solid rgba(59, 130, 246, 0.3)',
                        }}
                      >
                        CATS ATS
                      </span>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 600,
                      padding: '2px 6px',
                      borderRadius: '10px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      color: '#34d399',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                    }}
                  >
                    Active
                  </span>
                </div>

                <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  {job.title}
                </h4>

                <p
                  style={{
                    fontSize: '0.8rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.45,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    flex: 1,
                    margin: 0,
                  }}
                  title={job.description}
                >
                  {job.description}
                </p>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    fontSize: '0.76rem',
                    color: 'var(--text-muted)',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={12} /> {job.location}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> {job.employment_type}
                  </span>
                </div>

                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', marginTop: '4px' }}>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    style={{
                      width: '100%',
                      justifyContent: 'center',
                      gap: '6px',
                      padding: '7px 12px',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/employee/submit?positionId=${encodeURIComponent(job.id)}`, {
                        state: { positionId: job.id },
                      });
                    }}
                  >
                    <PlusCircle size={14} /> Refer for this Role
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
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
              Candidate Referrals
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Candidates recommended to open positions across Tangentia
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', maxWidth: '360px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search
                size={16}
                color="var(--text-muted)"
                style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
              />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '36px', width: '100%' }}
                placeholder="Search candidate or position..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>

        {isLoading && referrals.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading referrals...
          </div>
        ) : filteredReferrals.length === 0 ? (
          <div style={{ padding: '48px 20px', textAlign: 'center' }}>
            <FileText size={40} color="var(--text-muted)" style={{ margin: '0 auto 12px auto' }} />
            <h4 style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>No referrals found</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '18px' }}>
              No candidate referrals matching this criteria found.
            </p>
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate('submit-referral')}>
              <PlusCircle size={14} /> Submit New Referral
            </button>
          </div>
        ) : (
          <>
            <div className="table-scroll-hint">
              <span>⇄ Swipe horizontally to view full table details</span>
            </div>
            <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Referral ID</th>
                  <th>Candidate</th>
                  <th>Position</th>
                  <th>Referred By</th>
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
        </>
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width: '100%', flexWrap: 'wrap', gap: '8px' }}>
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
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Candidate Header Summary */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '10px',
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
            <div className="responsive-info-grid" style={{ gap: '12px', fontSize: '0.86rem' }}>
              <div><strong>Email:</strong> {selectedReferral.candidate_email}</div>
              <div><strong>Phone:</strong> {selectedReferral.candidate_phone}</div>
              <div><strong>Referred By:</strong> {selectedReferral.referred_by_name || 'N/A'} {selectedReferral.referred_by_email && `(${selectedReferral.referred_by_email})`}</div>
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
            {Boolean(selectedReferral.referral_note && selectedReferral.referral_note.trim()) && (
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
            )}

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
