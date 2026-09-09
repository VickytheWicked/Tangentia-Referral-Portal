import React, { useEffect, useState } from 'react';
import { AnalyticsResponse } from '../../types';
import { api } from '../../services/api';
import {
  BarChart3,
  TrendingUp,
  Award,
  Users,
  CheckCircle,
  Building,
  Calendar,
} from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      setIsLoading(true);
      try {
        const data = await api.getAnalytics();
        setAnalytics(data);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadAnalytics();
  }, []);

  if (isLoading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Aggregating enterprise referral analytics...
      </div>
    );
  }

  if (!analytics) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        No analytics data available.
      </div>
    );
  }

  const hireRate =
    analytics.total_referrals > 0
      ? Math.round((analytics.hired_referrals / analytics.total_referrals) * 100)
      : 0;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Header Summary */}
      <div className="metric-grid">
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Total Referrals</span>
            <Users size={20} color="#3b82f6" />
          </div>
          <span className="metric-value">{analytics.total_referrals}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">In Active Pipeline</span>
            <TrendingUp size={20} color="#f59e0b" />
          </div>
          <span className="metric-value">{analytics.active_referrals}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Hired Candidates</span>
            <CheckCircle size={20} color="#10b981" />
          </div>
          <span className="metric-value">{analytics.hired_referrals}</span>
        </div>

        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-label">Overall Hire Rate</span>
            <Award size={20} color="#ec4899" />
          </div>
          <span className="metric-value">{hireRate}%</span>
        </div>
      </div>

      {/* Referral Conversion Funnel */}
      <div className="card">
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Candidate Referral Conversion Funnel
        </h3>
        <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Step-by-step pipeline progression from employee submission to final hire
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {analytics.funnel.map((step, idx) => {
            const widthPct = Math.max(step.percentage, 5);
            return (
              <div key={step.status} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.86rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {idx + 1}. {step.status}
                  </span>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    <strong>{step.count}</strong> candidates ({step.percentage}%)
                  </span>
                </div>

                <div
                  style={{
                    height: '12px',
                    width: '100%',
                    background: 'var(--bg-secondary)',
                    borderRadius: '6px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${widthPct}%`,
                      background:
                        step.status === 'Hired'
                          ? 'linear-gradient(90deg, #10b981, #059669)'
                          : 'linear-gradient(90deg, #3b82f6, #60a5fa)',
                      borderRadius: '6px',
                      transition: 'width 0.6s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Section: Department Breakdown & Top Referrers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 340px), 1fr))', gap: '24px' }}>
        {/* Department Breakdown */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Building size={18} color="#60a5fa" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Referrals by Department
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {analytics.by_department.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>No department statistics.</div>
            ) : (
              analytics.by_department.map((dept) => (
                <div
                  key={dept.department}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    background: 'var(--bg-secondary)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                      {dept.department}
                    </div>
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                      {dept.hired_count} hired from referrals
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: '1rem',
                      fontWeight: 700,
                      color: '#93c5fd',
                      background: 'rgba(59, 130, 246, 0.1)',
                      padding: '4px 10px',
                      borderRadius: '8px',
                    }}
                  >
                    {dept.total_referrals}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Top Referrers Leaderboard */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Award size={18} color="#f59e0b" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Top Referrers Leaderboard
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {analytics.top_referrers.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>No leaderboard data available.</div>
            ) : (
              analytics.top_referrers.map((ref, idx) => (
                <div
                  key={ref.user_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    background: 'var(--bg-secondary)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span
                      style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        background: idx === 0 ? '#f59e0b' : idx === 1 ? '#94a3b8' : idx === 2 ? '#b45309' : 'rgba(255,255,255,0.1)',
                        color: idx < 3 ? '#000' : 'var(--text-secondary)',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {idx + 1}
                    </span>
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                        {ref.user_name}
                      </div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        {ref.user_email}
                      </div>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                      {ref.referral_count} submissions
                    </div>
                    <div style={{ fontSize: '0.74rem', color: '#10b981' }}>
                      {ref.hired_count} hired
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
