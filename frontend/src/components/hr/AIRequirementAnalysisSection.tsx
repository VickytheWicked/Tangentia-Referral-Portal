import React, { useState, useMemo } from 'react';
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  ChevronDown,
  ChevronUp,
  Info,
  Briefcase,
  FileText,
  ArrowRightLeft,
  Clock,
  Check,
  Filter,
} from 'lucide-react';
import { OverallAnalysis, RequirementAnalysisItem, RequirementStatus } from '../../types/cv_intelligence';

interface AIRequirementAnalysisSectionProps {
  analysis: OverallAnalysis;
  candidateName?: string;
  positionTitle?: string;
  positionId?: string;
  fitSummary?: string | null;
  matchLevel?: string | null;
  experienceMatch?: string | null;
  matchedSkills?: string[];
  missingSkills?: string[];
}

// ---------------------------------------------------------------------------
// Status configuration
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<RequirementStatus, {
  icon: React.ReactNode;
  label: string;
  differenceLabel: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
  pillBg: string;
  resumeBorder: string;
  resumeBg: string;
}> = {
  SUPPORTED: {
    icon: <CheckCircle2 size={15} />,
    label: 'Supported in Resume',
    differenceLabel: 'Alignment: Directly verified in candidate resume',
    textColor: '#34d399',
    bgColor: 'rgba(16, 185, 129, 0.08)',
    borderColor: 'rgba(16, 185, 129, 0.35)',
    pillBg: 'rgba(16, 185, 129, 0.18)',
    resumeBorder: 'rgba(16, 185, 129, 0.4)',
    resumeBg: 'rgba(16, 185, 129, 0.07)',
  },
  NOT_MET: {
    icon: <XCircle size={15} />,
    label: 'Not Met',
    differenceLabel: 'Difference: Below mandatory CATS One threshold',
    textColor: '#f87171',
    bgColor: 'rgba(239, 68, 68, 0.08)',
    borderColor: 'rgba(239, 68, 68, 0.35)',
    pillBg: 'rgba(239, 68, 68, 0.18)',
    resumeBorder: 'rgba(239, 68, 68, 0.4)',
    resumeBg: 'rgba(239, 68, 68, 0.07)',
  },
  NOT_DEMONSTRATED: {
    icon: <AlertTriangle size={15} />,
    label: 'Not Demonstrated in Resume',
    differenceLabel: 'Difference: Required by CATS One but not documented in resume',
    textColor: '#fbbf24',
    bgColor: 'rgba(245, 158, 11, 0.06)',
    borderColor: 'rgba(245, 158, 11, 0.3)',
    pillBg: 'rgba(245, 158, 11, 0.15)',
    resumeBorder: 'rgba(245, 158, 11, 0.3)',
    resumeBg: 'rgba(245, 158, 11, 0.05)',
  },
  PARTIALLY_SUPPORTED: {
    icon: <MinusCircle size={15} />,
    label: 'Partially Supported',
    differenceLabel: 'Difference: Partial alignment with requested criteria',
    textColor: '#fb923c',
    bgColor: 'rgba(249, 115, 22, 0.08)',
    borderColor: 'rgba(249, 115, 22, 0.35)',
    pillBg: 'rgba(249, 115, 22, 0.18)',
    resumeBorder: 'rgba(249, 115, 22, 0.35)',
    resumeBg: 'rgba(249, 115, 22, 0.06)',
  },
};

// ---------------------------------------------------------------------------
// Side-by-Side Requirement Comparison Card
// ---------------------------------------------------------------------------

interface ComparisonCardProps {
  item: RequirementAnalysisItem;
  index: number;
}

const RequirementComparisonCard: React.FC<ComparisonCardProps> = ({ item, index }) => {
  const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.NOT_DEMONSTRATED;
  const isNoEvidence =
    item.cv_evidence.toLowerCase().startsWith('no explicit') ||
    item.cv_evidence.toLowerCase().startsWith('no evidence') ||
    item.status === 'NOT_DEMONSTRATED';

  return (
    <div
      style={{
        borderRadius: '10px',
        border: `1px solid ${cfg.borderColor}`,
        background: 'rgba(15, 23, 42, 0.75)',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Top Bar: Requirement Number, Name, Category and Match Status */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '10px',
          padding: '12px 16px',
          background: 'rgba(30, 41, 59, 0.6)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
          <span
            style={{
              fontSize: '0.74rem',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'rgba(59, 130, 246, 0.18)',
              color: '#93c5fd',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              flexShrink: 0,
            }}
          >
            REQ #{index + 1}
          </span>
          <span
            style={{
              fontWeight: 700,
              fontSize: '0.94rem',
              color: '#f8fafc',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={item.requirement}
          >
            {item.requirement}
          </span>
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: '6px',
              background: 'rgba(148, 163, 184, 0.12)',
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              flexShrink: 0,
            }}
          >
            {item.category.replace(/_/g, ' ')}
          </span>
        </div>

        {/* Status Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.74rem',
            fontWeight: 700,
            padding: '3px 10px',
            borderRadius: '12px',
            background: cfg.pillBg,
            color: cfg.textColor,
            border: `1px solid ${cfg.borderColor}`,
            flexShrink: 0,
          }}
        >
          {cfg.icon}
          <span>{cfg.label}</span>
        </div>
      </div>

      {/* Main Dual-Column Comparison: CATS One vs Resume */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '12px',
          padding: '14px 16px',
        }}
      >
        {/* Left Column: CATS One Job Requirement */}
        <div
          style={{
            borderRadius: '8px',
            border: '1px solid rgba(56, 189, 248, 0.28)',
            background: 'rgba(14, 165, 233, 0.07)',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.74rem',
              fontWeight: 700,
              color: '#38bdf8',
              textTransform: 'uppercase',
              letterSpacing: '0.6px',
            }}
          >
            <Briefcase size={13} color="#38bdf8" />
            <span>CATS One Requirement</span>
          </div>

          <div
            style={{
              fontSize: '0.88rem',
              fontWeight: 600,
              color: '#f8fafc',
              lineHeight: 1.45,
            }}
          >
            {item.required_value}
          </div>

          <div style={{ fontSize: '0.73rem', color: '#94a3b8', marginTop: 'auto' }}>
            Job Opening Specification
          </div>
        </div>

        {/* Right Column: Candidate Resume Documentation */}
        <div
          style={{
            borderRadius: '8px',
            border: `1px solid ${cfg.resumeBorder}`,
            background: cfg.resumeBg,
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.74rem',
              fontWeight: 700,
              color: cfg.textColor,
              textTransform: 'uppercase',
              letterSpacing: '0.6px',
            }}
          >
            <FileText size={13} color={cfg.textColor} />
            <span>Documented in Resume</span>
          </div>

          <div
            style={{
              fontSize: '0.86rem',
              color: isNoEvidence ? '#94a3b8' : '#e2e8f0',
              fontStyle: isNoEvidence ? 'italic' : 'normal',
              lineHeight: 1.45,
            }}
          >
            {isNoEvidence ? (
              item.cv_evidence
            ) : (
              <span>“{item.cv_evidence}”</span>
            )}
          </div>

          <div style={{ fontSize: '0.73rem', color: '#94a3b8', marginTop: 'auto' }}>
            Extracted Resume Documentation
          </div>
        </div>
      </div>

      {/* Difference / Assessment Footer Callout */}
      <div
        style={{
          padding: '10px 16px',
          background: 'rgba(15, 23, 42, 0.45)',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              fontSize: '0.73rem',
              fontWeight: 800,
              color: cfg.textColor,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            {cfg.differenceLabel}
          </span>
        </div>
        {item.reasoning && (
          <div style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.45 }}>
            {item.reasoning}
          </div>
        )}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main AI Requirement Analysis Component
// ---------------------------------------------------------------------------

export const AIRequirementAnalysisSection: React.FC<AIRequirementAnalysisSectionProps> = ({
  analysis,
  candidateName,
  positionTitle,
  positionId,
  fitSummary,
  matchLevel,
  experienceMatch,
  matchedSkills = [],
  missingSkills = [],
}) => {
  const [showAll, setShowAll] = useState(false);
  const [filterType, setFilterType] = useState<'ALL' | 'SUPPORTED' | 'UNMET'>('ALL');

  // Prioritized list of all requirements:
  // 1. Mandatory requirements from CATS One (highest priority)
  // 2. Supported requirements (core skills demonstrated in resume)
  // 3. Partially supported requirements
  // 4. Not demonstrated requirements (missing evidence)
  const allPrioritizedRequirements = useMemo(() => {
    return [
      ...analysis.mandatory_requirements,
      ...analysis.supported_requirements,
      ...analysis.partially_supported_requirements,
      ...analysis.not_demonstrated_requirements,
    ];
  }, [analysis]);

  const filteredRequirements = useMemo(() => {
    if (filterType === 'SUPPORTED') {
      return allPrioritizedRequirements.filter(
        (r) => r.status === 'SUPPORTED' || r.status === 'PARTIALLY_SUPPORTED'
      );
    }
    if (filterType === 'UNMET') {
      return allPrioritizedRequirements.filter(
        (r) => r.status === 'NOT_DEMONSTRATED' || r.status === 'NOT_MET'
      );
    }
    return allPrioritizedRequirements;
  }, [allPrioritizedRequirements, filterType]);

  // First 5 to 6 requirements for the focused comparison
  const COMPARISON_LIMIT = 6;
  const displayedRequirements = useMemo(() => {
    if (showAll || filterType !== 'ALL') {
      return filteredRequirements;
    }
    return filteredRequirements.slice(0, COMPARISON_LIMIT);
  }, [filteredRequirements, showAll, filterType]);

  const totalCount = allPrioritizedRequirements.length;
  const supportedCount = analysis.supported_requirements.length;
  const partialCount = analysis.partially_supported_requirements.length;
  const notDemonstratedCount = analysis.not_demonstrated_requirements.length;
  const mandatoryCount = analysis.mandatory_requirements.length;

  return (
    <div
      style={{
        background: 'linear-gradient(180deg, rgba(30, 58, 138, 0.12) 0%, rgba(15, 23, 42, 0.4) 100%)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '12px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
      }}
    >
      {/* Header Row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ArrowRightLeft size={18} color="#60a5fa" />
            <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#93c5fd' }}>
              CATS One vs Resume — Requirements Comparison
            </h4>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '3px' }}>
            Side-by-side evidence comparison displaying differences between CATS One requirements and candidate resume
            {positionTitle && (
              <span style={{ color: '#cbd5e1' }}> for <strong>{positionTitle}</strong></span>
            )}
            {positionId && (
              <span style={{ color: '#60a5fa', marginLeft: '6px', fontFamily: 'var(--font-mono)' }}>({positionId})</span>
            )}
          </div>
        </div>

        {/* Requirements Scope Badge */}
        {totalCount > 0 && (
          <span
            style={{
              fontSize: '0.74rem',
              fontWeight: 700,
              padding: '3px 9px',
              borderRadius: '8px',
              background: 'rgba(59, 130, 246, 0.15)',
              color: '#60a5fa',
              border: '1px solid rgba(59, 130, 246, 0.3)',
            }}
          >
            {showAll || filterType !== 'ALL'
              ? `${filteredRequirements.length} Requirements`
              : `First ${Math.min(COMPARISON_LIMIT, totalCount)} of ${totalCount} Requirements`}
          </span>
        )}
      </div>

      {/* AI Fit Summary (Executive Evaluation) */}
      {fitSummary && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(59, 130, 246, 0.12)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            fontSize: '0.88rem',
            lineHeight: 1.5,
            color: '#e0f2fe',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}
        >
          <Sparkles size={16} color="#38bdf8" style={{ marginTop: '2px', flexShrink: 0 }} />
          <div>
            <strong style={{ color: '#93c5fd' }}>AI Fit Summary: </strong>
            <span style={{ fontStyle: 'italic' }}>{fitSummary}</span>
          </div>
        </div>
      )}

      {/* Experience & Skills Alignment Bar */}
      {(experienceMatch || matchedSkills.length > 0 || missingSkills.length > 0) && (
        <div
          style={{
            padding: '12px 14px',
            borderRadius: '8px',
            background: 'rgba(15, 23, 42, 0.55)',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}
        >
          {experienceMatch && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.84rem' }}>
              <Clock size={14} color="#60a5fa" />
              <strong style={{ color: '#93c5fd' }}>Experience Match:</strong>
              <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{experienceMatch}</span>
            </div>
          )}

          {matchedSkills.length > 0 && (
            <div>
              <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 700, color: '#34d399', letterSpacing: '0.5px' }}>
                Matched Skills in Resume ({matchedSkills.length}):
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                {matchedSkills.map((s, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: '0.76rem',
                      padding: '2px 8px',
                      borderRadius: '8px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      color: '#34d399',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      fontWeight: 600,
                    }}
                  >
                    ✓ {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {missingSkills.length > 0 && (
            <div>
              <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 700, color: '#fbbf24', letterSpacing: '0.5px' }}>
                Missing / Unmentioned Requirements ({missingSkills.length}):
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                {missingSkills.map((m, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: '0.76rem',
                      padding: '2px 8px',
                      borderRadius: '8px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#fbbf24',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      fontWeight: 600,
                    }}
                  >
                    • {m}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Metrics Summary Counters Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: '8px',
          padding: '10px 12px',
          borderRadius: '8px',
          background: 'rgba(15, 23, 42, 0.5)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Total Evaluated
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#93c5fd', marginTop: '1px' }}>
            {totalCount}
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Mandatory
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f87171', marginTop: '1px' }}>
            {mandatoryCount}
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Supported
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#34d399', marginTop: '1px' }}>
            {supportedCount}
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Partially Met
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fb923c', marginTop: '1px' }}>
            {partialCount}
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Missing / Unmet
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fbbf24', marginTop: '1px' }}>
            {notDemonstratedCount}
          </div>
        </div>
      </div>


      {/* Comparison Section Header & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {showAll || filterType !== 'ALL'
            ? `Requirements Comparison (${filteredRequirements.length})`
            : `First ${Math.min(COMPARISON_LIMIT, totalCount)} Requirements Comparison (CATS One vs Resume)`}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Quick Filter Buttons */}
          <div style={{ display: 'flex', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '6px', padding: '2px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <button
              onClick={() => setFilterType('ALL')}
              style={{
                background: filterType === 'ALL' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                border: 'none',
                color: filterType === 'ALL' ? '#93c5fd' : '#94a3b8',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              All
            </button>
            <button
              onClick={() => setFilterType('SUPPORTED')}
              style={{
                background: filterType === 'SUPPORTED' ? 'rgba(16, 185, 129, 0.25)' : 'transparent',
                border: 'none',
                color: filterType === 'SUPPORTED' ? '#34d399' : '#94a3b8',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Supported
            </button>
            <button
              onClick={() => setFilterType('UNMET')}
              style={{
                background: filterType === 'UNMET' ? 'rgba(245, 158, 11, 0.25)' : 'transparent',
                border: 'none',
                color: filterType === 'UNMET' ? '#fbbf24' : '#94a3b8',
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Gaps
            </button>
          </div>

          {/* Toggle All vs First 6 */}
          {totalCount > COMPARISON_LIMIT && filterType === 'ALL' && (
            <button
              onClick={() => setShowAll(!showAll)}
              style={{
                background: 'rgba(59, 130, 246, 0.15)',
                border: '1px solid rgba(59, 130, 246, 0.35)',
                borderRadius: '6px',
                color: '#93c5fd',
                fontSize: '0.76rem',
                fontWeight: 700,
                padding: '4px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                transition: 'all 0.15s ease',
              }}
            >
              <span>{showAll ? `Show First ${COMPARISON_LIMIT} Only` : `View All ${totalCount}`}</span>
              {showAll ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
          )}
        </div>
      </div>

      {/* Comparison Cards List */}
      {displayedRequirements.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {displayedRequirements.map((item, idx) => (
            <RequirementComparisonCard key={idx} item={item} index={idx} />
          ))}
        </div>
      ) : (
        <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
          No requirements match the selected filter.
        </p>
      )}

      {/* Expand Button at bottom if only showing top 6 */}
      {totalCount > COMPARISON_LIMIT && !showAll && filterType === 'ALL' && (
        <div style={{ textAlign: 'center', paddingTop: '4px' }}>
          <button
            onClick={() => setShowAll(true)}
            style={{
              background: 'transparent',
              border: '1px dashed rgba(59, 130, 246, 0.4)',
              borderRadius: '8px',
              color: '#60a5fa',
              fontSize: '0.8rem',
              fontWeight: 700,
              padding: '8px 16px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
            }}
          >
            <span>+ View {totalCount - COMPARISON_LIMIT} More Requirements</span>
            <ChevronDown size={14} />
          </button>
        </div>
      )}

      {/* Disclaimer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '6px',
          padding: '8px 12px',
          borderRadius: '6px',
          background: 'rgba(15, 23, 42, 0.35)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          fontSize: '0.74rem',
          color: 'var(--text-muted)',
          lineHeight: 1.4,
          marginTop: '4px',
        }}
      >
        <Info size={13} style={{ flexShrink: 0, marginTop: '1px', color: '#60a5fa' }} />
        <span>
          Comparisons reflect verbatim criteria from CATS One against documented evidence in the candidate's submitted CV.
          Assessments should be verified during interview screening.
        </span>
      </div>
    </div>
  );
};
