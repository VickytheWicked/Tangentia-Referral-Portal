import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  ChevronDown,
  ChevronRight,
  Info,
} from 'lucide-react';
import { OverallAnalysis, RequirementAnalysisItem, RequirementStatus } from '../../types/cv_intelligence';

interface AIRequirementAnalysisSectionProps {
  analysis: OverallAnalysis;
  candidateName?: string;
  positionTitle?: string;
}

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<RequirementStatus, {
  icon: React.ReactNode;
  label: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
  pillBg: string;
}> = {
  SUPPORTED: {
    icon: <CheckCircle2 size={16} />,
    label: 'Supported',
    textColor: '#34d399',
    bgColor: 'rgba(16, 185, 129, 0.06)',
    borderColor: 'rgba(16, 185, 129, 0.2)',
    pillBg: 'rgba(16, 185, 129, 0.15)',
  },
  NOT_MET: {
    icon: <XCircle size={16} />,
    label: 'Not Met',
    textColor: '#f87171',
    bgColor: 'rgba(239, 68, 68, 0.06)',
    borderColor: 'rgba(239, 68, 68, 0.2)',
    pillBg: 'rgba(239, 68, 68, 0.15)',
  },
  NOT_DEMONSTRATED: {
    icon: <AlertTriangle size={16} />,
    label: 'Not Demonstrated',
    textColor: '#fbbf24',
    bgColor: 'rgba(245, 158, 11, 0.06)',
    borderColor: 'rgba(245, 158, 11, 0.2)',
    pillBg: 'rgba(245, 158, 11, 0.15)',
  },
  PARTIALLY_SUPPORTED: {
    icon: <MinusCircle size={16} />,
    label: 'Partially Supported',
    textColor: '#fb923c',
    bgColor: 'rgba(249, 115, 22, 0.06)',
    borderColor: 'rgba(249, 115, 22, 0.2)',
    pillBg: 'rgba(249, 115, 22, 0.15)',
  },
};

// ---------------------------------------------------------------------------
// Individual requirement card
// ---------------------------------------------------------------------------

interface RequirementCardProps {
  item: RequirementAnalysisItem;
  showEvidence?: boolean;
}

const RequirementCard: React.FC<RequirementCardProps> = ({ item, showEvidence = false }) => {
  const [expanded, setExpanded] = useState(showEvidence);
  const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG['NOT_DEMONSTRATED'];

  return (
    <div
      style={{
        borderRadius: '8px',
        border: `1px solid ${cfg.borderColor}`,
        background: cfg.bgColor,
        overflow: 'hidden',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          padding: '10px 14px',
          cursor: 'pointer',
          userSelect: 'none',
        }}
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        {/* Status icon */}
        <span style={{ color: cfg.textColor, flexShrink: 0, marginTop: '1px' }}>
          {cfg.icon}
        </span>

        {/* Requirement name */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontWeight: 700,
            fontSize: '0.88rem',
            color: 'var(--text-primary)',
            lineHeight: 1.3,
          }}>
            {item.requirement}
          </div>
          <div style={{ fontSize: '0.77rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Required: {item.required_value}
          </div>
        </div>

        {/* Status pill */}
        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '10px',
            background: cfg.pillBg,
            color: cfg.textColor,
            border: `1px solid ${cfg.borderColor}`,
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          {cfg.label}
        </span>

        {/* Expand chevron */}
        <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
      </div>

      {/* Expandable evidence panel */}
      {expanded && (
        <div
          style={{
            borderTop: `1px solid ${cfg.borderColor}`,
            padding: '10px 14px 12px 40px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div>
            <span style={{ fontSize: '0.73rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              CV Evidence
            </span>
            <div style={{
              marginTop: '3px',
              fontSize: '0.83rem',
              color: item.cv_evidence.toLowerCase().startsWith('no explicit')
                ? 'var(--text-muted)'
                : '#e0f2fe',
              fontStyle: item.cv_evidence.toLowerCase().startsWith('no explicit') ? 'italic' : 'normal',
              lineHeight: 1.4,
            }}>
              {item.cv_evidence}
            </div>
          </div>
          {item.reasoning && (
            <div>
              <span style={{ fontSize: '0.73rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                Reasoning
              </span>
              <div style={{
                marginTop: '3px',
                fontSize: '0.82rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.4,
              }}>
                {item.reasoning}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Section header
// ---------------------------------------------------------------------------

interface SectionHeaderProps {
  title: string;
  count: number;
  color: string;
  icon: React.ReactNode;
  collapsed: boolean;
  onToggle: () => void;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ title, count, color, icon, collapsed, onToggle }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      marginBottom: collapsed ? 0 : '8px',
      cursor: 'pointer',
      userSelect: 'none',
    }}
    onClick={onToggle}
    role="button"
    tabIndex={0}
    onKeyDown={(e) => e.key === 'Enter' && onToggle()}
  >
    <span style={{ color }}>{icon}</span>
    <span style={{ fontSize: '0.82rem', fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.6px' }}>
      {title}
    </span>
    <span style={{
      fontSize: '0.72rem',
      fontWeight: 700,
      padding: '1px 7px',
      borderRadius: '10px',
      background: `rgba(${color === '#f87171' ? '239,68,68' : color === '#34d399' ? '16,185,129' : color === '#fb923c' ? '249,115,22' : '245,158,11'}, 0.15)`,
      color,
    }}>
      {count}
    </span>
    <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>
      {collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
    </span>
  </div>
);

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export const AIRequirementAnalysisSection: React.FC<AIRequirementAnalysisSectionProps> = ({
  analysis,
  candidateName,
  positionTitle,
}) => {
  const [mandatoryCollapsed, setMandatoryCollapsed] = useState(false);
  const [supportedCollapsed, setSupportedCollapsed] = useState(false);
  const [partialCollapsed, setPartialCollapsed] = useState(false);
  const [notDemonstratedCollapsed, setNotDemonstratedCollapsed] = useState(false);

  const hasAnyContent =
    analysis.mandatory_requirements.length > 0 ||
    analysis.supported_requirements.length > 0 ||
    analysis.partially_supported_requirements.length > 0 ||
    analysis.not_demonstrated_requirements.length > 0;

  return (
    <div
      style={{
        background: 'rgba(30, 58, 138, 0.08)',
        border: '1px solid rgba(59, 130, 246, 0.25)',
        borderRadius: '10px',
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Section header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Sparkles size={18} color="#60a5fa" />
        <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#93c5fd' }}>
          AI Requirement Analysis
        </h4>
        {candidateName && positionTitle && (
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: '4px' }}>
            — {candidateName} vs {positionTitle}
          </span>
        )}
      </div>

      {/* Disclaimer */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '6px',
        padding: '8px 12px',
        borderRadius: '6px',
        background: 'rgba(59, 130, 246, 0.08)',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        fontSize: '0.77rem',
        color: 'var(--text-muted)',
        lineHeight: 1.4,
      }}>
        <Info size={13} style={{ flexShrink: 0, marginTop: '1px', color: '#60a5fa' }} />
        <span>
          This analysis is based on the candidate's CV. It highlights what is <strong style={{ color: '#e0f2fe' }}>documented</strong>, not what the candidate may know.
          HR must independently verify all assessments before making a hiring decision.
        </span>
      </div>

      {/* Key Observations */}
      {analysis.key_observations && analysis.key_observations.length > 0 && (
        <div>
          <div style={{
            fontSize: '0.79rem',
            fontWeight: 700,
            color: '#93c5fd',
            textTransform: 'uppercase',
            letterSpacing: '0.6px',
            marginBottom: '8px',
          }}>
            Key Observations
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {analysis.key_observations.map((obs, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                fontSize: '0.86rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.4,
              }}>
                <span style={{ color: '#60a5fa', flexShrink: 0, fontWeight: 700, fontSize: '0.9rem', marginTop: '-1px' }}>•</span>
                <span>{obs}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!hasAnyContent && (
        <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
          No requirement analysis data available.
        </p>
      )}

      {/* Mandatory Requirements */}
      {analysis.mandatory_requirements.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(59, 130, 246, 0.15)', paddingTop: '14px' }}>
          <SectionHeader
            title="Mandatory Requirements"
            count={analysis.mandatory_requirements.length}
            color="#f87171"
            icon={<XCircle size={15} />}
            collapsed={mandatoryCollapsed}
            onToggle={() => setMandatoryCollapsed(!mandatoryCollapsed)}
          />
          {!mandatoryCollapsed && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {analysis.mandatory_requirements.map((item, idx) => (
                <RequirementCard key={idx} item={item} showEvidence={true} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Supported Requirements */}
      {analysis.supported_requirements.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(59, 130, 246, 0.15)', paddingTop: '14px' }}>
          <SectionHeader
            title="Supported Requirements"
            count={analysis.supported_requirements.length}
            color="#34d399"
            icon={<CheckCircle2 size={15} />}
            collapsed={supportedCollapsed}
            onToggle={() => setSupportedCollapsed(!supportedCollapsed)}
          />
          {!supportedCollapsed && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {analysis.supported_requirements.map((item, idx) => (
                <RequirementCard key={idx} item={item} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Partially Supported */}
      {analysis.partially_supported_requirements.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(59, 130, 246, 0.15)', paddingTop: '14px' }}>
          <SectionHeader
            title="Partially Supported"
            count={analysis.partially_supported_requirements.length}
            color="#fb923c"
            icon={<MinusCircle size={15} />}
            collapsed={partialCollapsed}
            onToggle={() => setPartialCollapsed(!partialCollapsed)}
          />
          {!partialCollapsed && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {analysis.partially_supported_requirements.map((item, idx) => (
                <RequirementCard key={idx} item={item} showEvidence={true} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Not Demonstrated */}
      {analysis.not_demonstrated_requirements.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(59, 130, 246, 0.15)', paddingTop: '14px' }}>
          <SectionHeader
            title="Not Demonstrated"
            count={analysis.not_demonstrated_requirements.length}
            color="#fbbf24"
            icon={<AlertTriangle size={15} />}
            collapsed={notDemonstratedCollapsed}
            onToggle={() => setNotDemonstratedCollapsed(!notDemonstratedCollapsed)}
          />
          {!notDemonstratedCollapsed && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {analysis.not_demonstrated_requirements.map((item, idx) => (
                <span
                  key={idx}
                  title={`Required: ${item.required_value}\n${item.cv_evidence}`}
                  style={{
                    fontSize: '0.78rem',
                    padding: '3px 10px',
                    borderRadius: '10px',
                    background: 'rgba(245, 158, 11, 0.12)',
                    color: '#fbbf24',
                    border: '1px solid rgba(245, 158, 11, 0.25)',
                    fontWeight: 600,
                    cursor: 'default',
                  }}
                >
                  • {item.requirement}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
