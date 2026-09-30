import React, { useEffect, useState } from 'react';
import { ReferralSummary, AnalyticsResponse } from '../../types';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';
import {
  Users,
  Clock,
  Award,
  CheckCircle,
  Briefcase,
  BarChart3,
  ExternalLink,
  Download,
  Search,
  Filter,
} from 'lucide-react';
import { onReferralUpdated } from '../../services/referralEvents';

interface HRDashboardProps {
  onNavigate: (tab: string) => void;
  onOpenCandidate: (id: string) => void;
}

let cachedAnalytics: AnalyticsResponse | null = null;
let cachedRecentReferrals: ReferralSummary[] = [];

export const HRDashboard: React.FC<HRDashboardProps> = ({ onNavigate, onOpenCandidate }) => {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(() => cachedAnalytics);
  const [recentReferrals, setRecentReferrals] = useState<ReferralSummary[]>(() => cachedRecentReferrals);
  const [isLoading, setIsLoading] = useState<boolean>(() => !cachedAnalytics);

  const loadData = async (silent = false) => {
    if (!silent && !analytics && !cachedAnalytics) {
      setIsLoading(true);
    }
    try {
      const [anData, refData] = await Promise.all([
        api.getAnalytics(),
        api.getAllReferrals(),
      ]);
      // Guard metrics from dropping to zero during background processing or transient reloads
      if (anData && (anData.total_referrals > 0 || !cachedAnalytics || cachedAnalytics.total_referrals === 0)) {
        cachedAnalytics = anData;
        setAnalytics(anData);
      }
      if (Array.isArray(refData) && (refData.length > 0 || !silent || cachedRecentReferrals.length === 0)) {
        cachedRecentReferrals = refData.slice(0, 8);
        setRecentReferrals(cachedRecentReferrals);
      }
    } catch (err) {
      console.error('Failed to load HR dashboard data:', err);
    } finally {
      if (!silent) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    loadData();

    const unsubscribe = onReferralUpdated(() => {
      loadData(true);
    });

    const timer = setInterval(() => {
      loadData(true);
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(timer);
    };
  }, []);

  const handleDownloadCV = async (refId: string, filename: string) => {
    try {
      await api.downloadCV(refId, filename);
    } catch (err: any) {
      alert(err.message || 'Failed to download CV');
    }
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Banner */}
      <div
        className="card card-glass responsive-banner"
        style={{
          padding: '24px 28px',
          background: 'linear-gradient(135deg, rgba(88, 28, 135, 0.3) 0%, rgba(15, 23, 42, 0.7) 100%)',
          borderColor: 'rgba(139, 92, 246, 0.3)',
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
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#fff', marginBottom: '4px' }}>
            HR & Talent Acquisition Hub
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '640px', lineHeight: 1.5 }}>
            Review, evaluate, and track enterprise candidate referrals submitted by Tangentia employees.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => onNavigate('job-positions')}>
            <Briefcase size={16} /> Manage Job Openings
          </button>
          <button className="btn btn-primary" onClick={() => onNavigate('all-referrals')}>
            <Users size={16} /> View All Candidates
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metric-grid">
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Total Referrals</span>
            <Users size={20} color="#3b82f6" />
          </div>
          <span className="metric-value">{analytics?.total_referrals || 0}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Active Pipeline</span>
            <Clock size={20} color="#f59e0b" />
          </div>
          <span className="metric-value">{analytics?.active_referrals || 0}</span>
        </div>

        <div
          className="metric-card"
          style={{ cursor: 'pointer' }}
          onClick={() => onNavigate('hired-history')}
          title="View all hired candidates in Hired History"
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Hired Candidates</span>
            <CheckCircle size={20} color="#10b981" />
          </div>
          <span className="metric-value">{analytics?.hired_referrals || 0}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Conversion Rate</span>
            <Award size={20} color="#ec4899" />
          </div>
          <span className="metric-value">
            {analytics && analytics.total_referrals > 0
              ? `${Math.round((analytics.hired_referrals / analytics.total_referrals) * 100)}%`
              : '0%'}
          </span>
        </div>
      </div>

      {/* Funnel Pipeline Visual Strip */}
      {analytics && analytics.funnel && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Referral Pipeline Funnel
            </h3>
            <button className="btn btn-outline btn-sm" onClick={() => onNavigate('analytics')}>
              <BarChart3 size={14} /> Full Analytics
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
            {analytics.funnel.map((step) => (
              <div
                key={step.status}
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  {step.status}
                </span>
                <span style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {step.count}
                </span>
                <span style={{ fontSize: '0.72rem', color: '#60a5fa' }}>
                  {step.percentage}% of total
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Referrals Table */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Recent Submissions Requiring Action
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Latest candidate referrals submitted by employees
            </p>
          </div>

          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('all-referrals')}>
            View All Submissions
          </button>
        </div>

        {isLoading && recentReferrals.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading submissions...
          </div>
        ) : recentReferrals.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No submissions found.
          </div>
        ) : (
          <>
            <div className="table-scroll-hint">
              <span>⇄ Swipe horizontally to view candidate records</span>
            </div>
            <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Referral ID</th>
                  <th>Candidate</th>
                  <th>Position</th>
                  <th>Referred By</th>
                  <th>Submitted Date</th>
                  <th>Status</th>
                  <th>CV Document</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentReferrals.map((r) => (
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
                        title="Download candidate CV"
                      >
                        <Download size={14} /> Download
                      </button>
                    </td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => onOpenCandidate(r.id)}
                      >
                        <ExternalLink size={14} /> Manage Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
    </div>
  );
};
