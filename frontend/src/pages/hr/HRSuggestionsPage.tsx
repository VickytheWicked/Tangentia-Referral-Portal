import React, { useState, useEffect } from 'react';
import {
  Search,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Briefcase,
  MapPin,
  Users,
  Download,
  ExternalLink,
  Sparkles,
  Layers,
  AlertCircle,
  Star,
  CheckCircle2,
  Edit3,
} from 'lucide-react';
import { OpeningSuggestions, SuggestedCandidateSummary, CandidateProfileDetail } from '../../types/cv_intelligence';
import { ReferralStatusType } from '../../types';
import { api } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { CandidateIntelligenceModal } from '../../components/hr/CandidateIntelligenceModal';
import { StatusChangeModal } from '../../components/hr/StatusChangeModal';
import { HistoricalReferralsSection } from '../../components/hr/HistoricalReferralsSection';

export const HRSuggestionsPage: React.FC = () => {
  const [openings, setOpenings] = useState<OpeningSuggestions[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');

  // Keep ALL dropdowns closed initially
  const [expandedOpenings, setExpandedOpenings] = useState<Record<string, boolean>>({});


  const [selectedCandidate, setSelectedCandidate] = useState<CandidateProfileDetail | null>(null);
  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);
  const [statusCandidate, setStatusCandidate] = useState<SuggestedCandidateSummary | null>(null);
  const [featureDisabled, setFeatureDisabled] = useState<boolean>(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getHRSuggestions();
      setOpenings(data);
      // NOTE: Dropdowns remain closed initially per requirement
    } catch (err: any) {
      if (err.message && err.message.includes('disabled')) {
        setFeatureDisabled(true);
      } else {
        setError(err.message || 'Failed to load candidate suggestions.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleExpand = (positionId: string) => {
    setExpandedOpenings((prev) => ({
      ...prev,
      [positionId]: !prev[positionId],
    }));
  };

  const handleOpenCandidate = async (referralId: string) => {
    try {
      setLoadingDetailId(referralId);
      const detail = await api.getCandidateIntelligence(referralId);
      setSelectedCandidate(detail);
    } catch (err: any) {
      alert(`Failed to load candidate details: ${err.message || 'Unknown error'}`);
    } finally {
      setLoadingDetailId(null);
    }
  };



  const handleDownloadCV = async (e: React.MouseEvent, refId: string, filename: string) => {
    e.stopPropagation();
    try {
      await api.downloadCV(refId, filename);
    } catch (err: any) {
      alert(err.message || 'Failed to download CV');
    }
  };

  // Distinct departments
  const departments = ['ALL', ...Array.from(new Set(openings.map((o) => o.department))).filter(Boolean)];

  // Filter openings
  const filteredOpenings = openings.filter((op) => {
    const matchesDept = departmentFilter === 'ALL' || op.department === departmentFilter;
    const term = searchTerm.toLowerCase().trim();
    if (!term) return matchesDept;

    const matchesTitle = op.title.toLowerCase().includes(term);
    const matchesDeptName = op.department.toLowerCase().includes(term);
    const matchesCandidates = [
      ...op.strong_matches,
      ...op.good_matches,
      ...op.potential_matches,
      ...op.pending_extraction,
      ...op.failed_extraction,
    ].some(
      (c) =>
        c.candidate_name.toLowerCase().includes(term) ||
        c.candidate_email.toLowerCase().includes(term) ||
        c.matched_skills.some((s) => s.toLowerCase().includes(term))
    );

    return matchesDept && (matchesTitle || matchesDeptName || matchesCandidates);
  });

  // Sort openings: highest number of referrals first, tiebreak alphabetically by title
  const sortedOpenings = [...filteredOpenings].sort((a, b) => {
    if (b.total_candidates !== a.total_candidates) {
      return b.total_candidates - a.total_candidates;
    }
    return a.title.localeCompare(b.title);
  });

  const getMatchBadgeStyle = (level?: string, status?: string) => {
    if (level === 'Strong Match') return { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.3)', label: 'Strong Match' };
    if (level === 'Good Match') return { bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)', label: 'Good Match' };
    if (level === 'Potential Match') return { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)', label: 'Potential Match' };
    if (status === 'FAILED') return { bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: 'rgba(239, 68, 68, 0.3)', label: 'Failed' };
    return { bg: 'rgba(100, 116, 139, 0.15)', color: '#94a3b8', border: 'rgba(100, 116, 139, 0.3)', label: 'Pending Extraction' };
  };

  if (featureDisabled) {
    return (
      <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px', maxWidth: '600px', margin: '40px auto' }}>
          <div
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}
          >
            <AlertCircle size={30} color="#f87171" />
          </div>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Candidate Suggestions Feature is Disabled
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>
            This feature is currently deactivated. To enable it locally, set{' '}
            <code>CV_INTELLIGENCE_ENABLED=true</code> in your backend <code>.env</code> file.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card">
        {/* Page Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Candidate Suggestions
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Explainable candidate matching suggestions organized by open job requisitions
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={loadData}
              disabled={loading}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>

            <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Showing <strong>{sortedOpenings.length}</strong> of <strong>{openings.length}</strong> openings
            </span>
          </div>
        </div>

        {/* Filters Grid consistent with AllReferralsPage */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: '12px', marginBottom: '20px' }}>
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
              placeholder="Search by job title, candidate, or skill..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div>
            <select
              className="form-select"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
            >
              <option value="ALL">All Departments</option>
              {departments.filter((dept) => dept !== 'ALL').map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '0.86rem',
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#f87171',
              border: '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            {error}
          </div>
        )}

        {/* Openings Accordion List (Openings with most referrals placed on top) */}
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading candidate suggestions...
          </div>
        ) : sortedOpenings.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Briefcase size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
            <p style={{ margin: 0 }}>No job openings found matching your filter criteria.</p>
          </div>
        ) : (
          <div className="openings-scroll-container">
            {sortedOpenings.map((opening) => {
              const isExpanded = !!expandedOpenings[opening.position_id];
              const hasCandidates = opening.total_candidates > 0;

              // Priority-ordered referrals: Strong -> Good -> Potential -> Pending -> Failed
              // The candidate with the highest priority score is placed first
              const prioritizedCandidates: SuggestedCandidateSummary[] = [
                ...opening.strong_matches,
                ...opening.good_matches,
                ...opening.potential_matches,
                ...opening.pending_extraction,
                ...opening.failed_extraction,
              ].sort((a, b) => {
                const scoreA = a.priority_score ?? 0;
                const scoreB = b.priority_score ?? 0;
                if (scoreB !== scoreA) return scoreB - scoreA;
                if (b.matched_skills.length !== a.matched_skills.length) {
                  return b.matched_skills.length - a.matched_skills.length;
                }
                return b.years_of_experience - a.years_of_experience;
              });

              return (
                <div
                  key={opening.position_id}
                  style={{
                    borderRadius: '10px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-secondary)',
                    overflow: 'hidden',
                  }}
                >
                  {/* Opening Dropdown Header */}
                  <div
                    onClick={() => toggleExpand(opening.position_id)}
                    style={{
                      padding: '16px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      userSelect: 'none',
                      background: isExpanded ? 'rgba(30, 41, 59, 0.7)' : 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <button
                        className="btn btn-outline btn-sm"
                        style={{ padding: '4px', minWidth: '28px', minHeight: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                        aria-label="Toggle opening details"
                      >
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </button>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                          <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {opening.title}
                          </h4>
                          <span style={{ fontSize: '0.72rem', color: '#93c5fd', background: 'rgba(59, 130, 246, 0.15)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(59, 130, 246, 0.25)', fontWeight: 600 }}>
                            {opening.department}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <MapPin size={12} />
                            {opening.location}
                          </span>
                          <span>•</span>
                          <span>{opening.employment_type}</span>
                          {opening.min_experience_years > 0 && (
                            <>
                              <span>•</span>
                              <span>Target: {opening.min_experience_years}+ yrs</span>
                            </>
                          )}
                          <span>•</span>
                          <span style={{ fontWeight: 600, color: hasCandidates ? '#60a5fa' : 'inherit' }}>
                            {opening.total_candidates} referred candidate{opening.total_candidates !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                    </div>


                  </div>

                  {/* Expanded Content: NEW REFERRALS and OLD REFERRALS */}
                  {isExpanded && (
                    <div style={{ padding: '20px', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '18px' }}>
                      {/* 1. Candidate Referrals for Current Opening */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                          <h5 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Users size={16} color="var(--primary)" />
                            NEW REFERRALS ({prioritizedCandidates.length})
                          </h5>
                        </div>

                        {!hasCandidates ? (
                          <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
                            No candidates have been referred for this opening yet.
                          </div>
                        ) : (
                          <>
                            {/* Desktop Data Table */}
                            <div className="table-container hidden-mobile" style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '480px', width: '100%', WebkitOverflowScrolling: 'touch', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                            <table className="data-table" style={{ width: '100%', minWidth: '960px' }}>
                              <thead>
                                <tr>
                                  <th style={{ width: '135px', minWidth: '135px', whiteSpace: 'nowrap' }}>Priority</th>
                                  <th style={{ minWidth: '150px' }}>Candidate</th>
                                  <th style={{ width: '110px', minWidth: '110px', whiteSpace: 'nowrap' }}>Match Level</th>
                                  <th style={{ width: '85px', minWidth: '85px', whiteSpace: 'nowrap' }}>Experience</th>
                                  <th style={{ minWidth: '140px', maxWidth: '180px' }}>Matched Criteria</th>
                                  <th style={{ minWidth: '170px', maxWidth: '220px' }}>Decision Highlight</th>
                                  <th style={{ width: '110px', minWidth: '110px', whiteSpace: 'nowrap' }}>Status</th>
                                  <th style={{ width: '170px', minWidth: '170px', textAlign: 'right', whiteSpace: 'nowrap', paddingRight: '16px' }}>Actions</th>
                                </tr>
                              </thead>
                              <tbody>
                                {prioritizedCandidates.map((c, idx) => {
                                  const badge = getMatchBadgeStyle(c.match_level, c.extraction_status);
                                  const isFirstPriority = idx === 0 && (c.match_level === 'Strong Match' || c.match_level === 'Good Match' || c.match_level === 'Potential Match');

                                  return (
                                    <tr
                                      key={c.referral_id}
                                      onClick={() => handleOpenCandidate(c.referral_id)}
                                      style={{
                                        cursor: 'pointer',
                                        background: isFirstPriority ? 'rgba(234, 179, 8, 0.05)' : undefined,
                                      }}
                                    >
                                      <td>
                                        {isFirstPriority ? (
                                          <span
                                            style={{
                                              display: 'inline-flex',
                                              alignItems: 'center',
                                              gap: '4px',
                                              padding: '4px 10px',
                                              borderRadius: '20px',
                                              fontSize: '0.74rem',
                                              fontWeight: 800,
                                              background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.22), rgba(245, 158, 11, 0.32))',
                                              color: '#fbbf24',
                                              border: '1px solid rgba(245, 158, 11, 0.55)',
                                              boxShadow: '0 0 10px rgba(245, 158, 11, 0.15)',
                                              whiteSpace: 'nowrap',
                                            }}
                                          >
                                            <Star size={12} fill="#fbbf24" /> #1 High Priority
                                          </span>
                                        ) : idx === 1 ? (
                                          <span
                                            style={{
                                              display: 'inline-flex',
                                              alignItems: 'center',
                                              padding: '3px 8px',
                                              borderRadius: '12px',
                                              fontSize: '0.74rem',
                                              fontWeight: 700,
                                              background: 'rgba(59, 130, 246, 0.18)',
                                              color: '#93c5fd',
                                              border: '1px solid rgba(59, 130, 246, 0.35)',
                                              whiteSpace: 'nowrap',
                                            }}
                                          >
                                            #2 Priority
                                          </span>
                                        ) : idx === 2 ? (
                                          <span
                                            style={{
                                              display: 'inline-flex',
                                              alignItems: 'center',
                                              padding: '3px 8px',
                                              borderRadius: '12px',
                                              fontSize: '0.74rem',
                                              fontWeight: 600,
                                              background: 'rgba(100, 116, 139, 0.2)',
                                              color: '#cbd5e1',
                                              border: '1px solid rgba(148, 163, 184, 0.25)',
                                              whiteSpace: 'nowrap',
                                            }}
                                          >
                                            #3 Priority
                                          </span>
                                        ) : (
                                          <span
                                            style={{
                                              fontSize: '0.74rem',
                                              color: 'var(--text-muted)',
                                              padding: '2px 8px',
                                              fontWeight: 500,
                                            }}
                                          >
                                            #{idx + 1}
                                          </span>
                                        )}
                                      </td>
                                      <td>
                                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                          {c.candidate_name}
                                        </div>
                                        <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                                          {c.candidate_email}
                                        </div>
                                        {c.fit_summary && (
                                          <div
                                            style={{
                                              marginTop: '5px',
                                              fontSize: '0.74rem',
                                              color: '#cbd5e1',
                                              lineHeight: '1.35',
                                              display: 'flex',
                                              alignItems: 'flex-start',
                                              gap: '5px',
                                              background: 'rgba(30, 41, 59, 0.45)',
                                              padding: '4px 8px',
                                              borderRadius: '6px',
                                              borderLeft: '2px solid #38bdf8',
                                              maxWidth: '300px',
                                            }}
                                            title={c.fit_summary}
                                          >
                                            <Sparkles size={11} color="#38bdf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                                            <span
                                              style={{
                                                display: '-webkit-box',
                                                WebkitLineClamp: 2,
                                                WebkitBoxOrient: 'vertical',
                                                overflow: 'hidden',
                                                fontStyle: 'italic',
                                              }}
                                            >
                                              {c.fit_summary}
                                            </span>
                                          </div>
                                        )}
                                      </td>
                                      <td>
                                        <span
                                          style={{
                                            fontSize: '0.74rem',
                                            padding: '2px 8px',
                                            borderRadius: '10px',
                                            background: badge.bg,
                                            color: badge.color,
                                            border: `1px solid ${badge.border}`,
                                            fontWeight: 700,
                                            whiteSpace: 'nowrap',
                                          }}
                                        >
                                          {badge.label}
                                        </span>
                                      </td>
                                      <td>
                                        <span style={{ fontSize: '0.84rem' }}>
                                          {c.years_of_experience > 0 ? `${c.years_of_experience} yrs` : 'N/A'}
                                        </span>
                                      </td>
                                      <td>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', maxWidth: '180px' }}>
                                          {c.matched_skills.slice(0, 3).map((s, sIdx) => (
                                            <span
                                              key={sIdx}
                                              style={{
                                                fontSize: '0.72rem',
                                                padding: '2px 6px',
                                                borderRadius: '4px',
                                                background: 'rgba(59, 130, 246, 0.15)',
                                                color: '#93c5fd',
                                              }}
                                            >
                                              {s}
                                            </span>
                                          ))}
                                          {c.matched_skills.length > 3 && (
                                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                                              +{c.matched_skills.length - 3}
                                            </span>
                                          )}
                                        </div>
                                      </td>
                                      <td>
                                        <div
                                          style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                          title={c.explanation && c.explanation.length > 0 ? c.explanation[0] : undefined}
                                        >
                                          {c.explanation && c.explanation.length > 0 ? c.explanation[0] : '—'}
                                        </div>
                                      </td>
                                      <td>
                                        <StatusBadge status={c.referral_status} />
                                      </td>
                                      <td style={{ width: '230px', minWidth: '230px', textAlign: 'right', whiteSpace: 'nowrap', paddingRight: '16px' }}>
                                        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }} onClick={(e) => e.stopPropagation()}>
                                          <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => handleOpenCandidate(c.referral_id)}
                                            disabled={loadingDetailId === c.referral_id}
                                            title="View Complete Candidate Dossier"
                                            style={{ whiteSpace: 'nowrap' }}
                                          >
                                            <ExternalLink size={13} /> {loadingDetailId === c.referral_id ? 'Loading...' : 'Profile'}
                                          </button>
                                          <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => setStatusCandidate(c)}
                                            title="Change Referral Status"
                                            style={{ whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                                          >
                                            <Edit3 size={13} /> Status
                                          </button>
                                          <button
                                            className="btn btn-outline btn-sm"
                                            onClick={(e) => handleDownloadCV(e, c.referral_id, c.original_filename)}
                                            title="Download CV"
                                            style={{ whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                                          >
                                            <Download size={13} /> CV
                                          </button>

                                        </div>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>

                          {/* Mobile Candidate Cards */}
                          <div className="visible-mobile" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {prioritizedCandidates.map((c, idx) => {
                              const badge = getMatchBadgeStyle(c.match_level, c.extraction_status);
                              const isFirstPriority = idx === 0 && (c.match_level === 'Strong Match' || c.match_level === 'Good Match' || c.match_level === 'Potential Match');

                              return (
                                <div
                                  key={c.referral_id}
                                  onClick={() => handleOpenCandidate(c.referral_id)}
                                  style={{
                                    padding: '14px',
                                    borderRadius: '10px',
                                    background: isFirstPriority
                                      ? 'linear-gradient(135deg, rgba(234, 179, 8, 0.08), rgba(30, 41, 59, 0.7))'
                                      : 'rgba(30, 41, 59, 0.6)',
                                    border: isFirstPriority
                                      ? '1px solid rgba(245, 158, 11, 0.45)'
                                      : '1px solid var(--border-subtle)',
                                    boxShadow: isFirstPriority
                                      ? '0 2px 12px rgba(245, 158, 11, 0.1)'
                                      : 'none',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '10px',
                                    cursor: 'pointer',
                                  }}
                                >
                                  {/* Header: Priority & Match Level */}
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                                    <div>
                                      {isFirstPriority ? (
                                        <span
                                          style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '3px 9px',
                                            borderRadius: '16px',
                                            fontSize: '0.72rem',
                                            fontWeight: 800,
                                            background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.22), rgba(245, 158, 11, 0.32))',
                                            color: '#fbbf24',
                                            border: '1px solid rgba(245, 158, 11, 0.55)',
                                            boxShadow: '0 0 8px rgba(245, 158, 11, 0.15)',
                                          }}
                                        >
                                          <Star size={11} fill="#fbbf24" /> #1 High Priority
                                        </span>
                                      ) : idx === 1 ? (
                                        <span
                                          style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            padding: '2px 8px',
                                            borderRadius: '10px',
                                            fontSize: '0.72rem',
                                            fontWeight: 700,
                                            background: 'rgba(59, 130, 246, 0.18)',
                                            color: '#93c5fd',
                                            border: '1px solid rgba(59, 130, 246, 0.35)',
                                          }}
                                        >
                                          #2 Priority
                                        </span>
                                      ) : idx === 2 ? (
                                        <span
                                          style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            padding: '2px 8px',
                                            borderRadius: '10px',
                                            fontSize: '0.72rem',
                                            fontWeight: 600,
                                            background: 'rgba(100, 116, 139, 0.2)',
                                            color: '#cbd5e1',
                                            border: '1px solid rgba(148, 163, 184, 0.25)',
                                          }}
                                        >
                                          #3 Priority
                                        </span>
                                      ) : (
                                        <span
                                          style={{
                                            fontSize: '0.72rem',
                                            color: 'var(--text-muted)',
                                            padding: '2px 6px',
                                            fontWeight: 600,
                                          }}
                                        >
                                          #{idx + 1}
                                        </span>
                                      )}
                                    </div>

                                    <span
                                      style={{
                                        fontSize: '0.72rem',
                                        padding: '2px 8px',
                                        borderRadius: '8px',
                                        background: badge.bg,
                                        color: badge.color,
                                        border: `1px solid ${badge.border}`,
                                        fontWeight: 700,
                                        whiteSpace: 'nowrap',
                                      }}
                                    >
                                      {badge.label}
                                    </span>
                                  </div>

                                  {/* Candidate Identity */}
                                  <div>
                                    <div style={{ fontWeight: 700, fontSize: '0.98rem', color: 'var(--text-primary)' }}>
                                      {c.candidate_name}
                                    </div>
                                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                      {c.candidate_email}
                                    </div>
                                    {c.fit_summary && (
                                      <div
                                        style={{
                                          marginTop: '6px',
                                          fontSize: '0.78rem',
                                          color: '#e2e8f0',
                                          lineHeight: '1.4',
                                          display: 'flex',
                                          alignItems: 'flex-start',
                                          gap: '6px',
                                          background: 'rgba(15, 23, 42, 0.55)',
                                          padding: '6px 10px',
                                          borderRadius: '6px',
                                          borderLeft: '3px solid #38bdf8',
                                          fontStyle: 'italic',
                                        }}
                                      >
                                        <Sparkles size={13} color="#38bdf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                                        <span>{c.fit_summary}</span>
                                      </div>
                                    )}
                                  </div>

                                  {/* Metrics: Experience & Status */}
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                      Experience: <strong style={{ color: 'var(--text-primary)' }}>{c.years_of_experience > 0 ? `${c.years_of_experience} yrs` : 'N/A'}</strong>
                                    </span>
                                    <StatusBadge status={c.referral_status} />
                                  </div>

                                  {/* Matched Skills */}
                                  {c.matched_skills.length > 0 && (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                      {c.matched_skills.slice(0, 4).map((s, sIdx) => (
                                        <span
                                          key={sIdx}
                                          style={{
                                            fontSize: '0.7rem',
                                            padding: '2px 7px',
                                            borderRadius: '4px',
                                            background: 'rgba(59, 130, 246, 0.15)',
                                            color: '#93c5fd',
                                            border: '1px solid rgba(59, 130, 246, 0.25)',
                                          }}
                                        >
                                          {s}
                                        </span>
                                      ))}
                                      {c.matched_skills.length > 4 && (
                                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                                          +{c.matched_skills.length - 4} more
                                        </span>
                                      )}
                                    </div>
                                  )}

                                  {/* Decision Highlight / Explanation */}
                                  {c.explanation && c.explanation.length > 0 && (
                                    <div
                                      style={{
                                        fontSize: '0.78rem',
                                        color: 'var(--text-secondary)',
                                        padding: '8px 10px',
                                        borderRadius: '6px',
                                        background: 'rgba(15, 23, 42, 0.45)',
                                        borderLeft: '3px solid #3b82f6',
                                        lineHeight: '1.4',
                                      }}
                                    >
                                      {c.explanation[0]}
                                    </div>
                                  )}

                                  {/* Mobile Action Buttons */}
                                  <div
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingTop: '4px', flexWrap: 'wrap' }}
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <button
                                      className="btn btn-secondary btn-sm"
                                      style={{ flex: 1, minWidth: '85px', justifyContent: 'center', gap: '4px', fontSize: '0.78rem' }}
                                      onClick={() => handleOpenCandidate(c.referral_id)}
                                      disabled={loadingDetailId === c.referral_id}
                                    >
                                      <ExternalLink size={13} />
                                      <span>{loadingDetailId === c.referral_id ? 'Loading...' : 'Profile'}</span>
                                    </button>

                                    <button
                                      className="btn btn-secondary btn-sm"
                                      style={{ flex: 1, minWidth: '85px', justifyContent: 'center', gap: '4px', fontSize: '0.78rem' }}
                                      onClick={() => setStatusCandidate(c)}
                                    >
                                      <Edit3 size={13} />
                                      <span>Status</span>
                                    </button>

                                    <button
                                      className="btn btn-outline btn-sm"
                                      style={{ minWidth: '40px', padding: '5px 10px', justifyContent: 'center', gap: '4px', fontSize: '0.78rem' }}
                                      onClick={(e) => handleDownloadCV(e, c.referral_id, c.original_filename)}
                                      title="Download CV"
                                    >
                                      <Download size={13} />
                                      <span>CV</span>
                                    </button>


                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </>
                      )}
                      </div>

                      {/* 3. Historical Referral Suggestions (Isolated Old Referrals Section) */}
                      <HistoricalReferralsSection
                        positionId={opening.position_id}
                        currentPositionTitle={opening.title}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Candidate Dossier Modal */}
      {selectedCandidate && (
        <CandidateIntelligenceModal
          profile={selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
          onProfileUpdated={(updated) => {
            setSelectedCandidate(updated);
            loadData();
          }}
        />
      )}

      {/* Quick Status Change Modal from table row */}
      {statusCandidate && (
        <StatusChangeModal
          isOpen={true}
          onClose={() => setStatusCandidate(null)}
          referralId={statusCandidate.referral_id}
          candidateName={statusCandidate.candidate_name}
          currentStatus={statusCandidate.referral_status as ReferralStatusType}
          onStatusUpdated={() => {
            loadData();
          }}
        />
      )}
    </div>
  );
};
