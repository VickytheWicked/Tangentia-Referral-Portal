import React, { useEffect, useState } from 'react';
import { HiredHistoryItem } from '../../types';
import { api } from '../../services/api';
import {
  Award,
  Search,
  Briefcase,
  MapPin,
  Calendar,
  UserCheck,
  Building,
  CheckCircle2,
  Lock,
  Clock,
  Filter,
  FileSpreadsheet,
} from 'lucide-react';

export const HiredHistoryPage: React.FC = () => {
  const [history, setHistory] = useState<HiredHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');

  const handleExportExcel = async () => {
    try {
      setIsExporting(true);
      await api.downloadHiredHistoryExcel();
    } catch (err: any) {
      alert(err.message || 'Failed to export Hired Referral History in Excel.');
    } finally {
      setIsExporting(false);
    }
  };


  const fetchHiredHistory = async () => {
    setIsLoading(true);
    try {
      const data = await api.getHiredHistory();
      setHistory(data);
    } catch (err) {
      console.error('Failed to load hired history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHiredHistory();
  }, []);

  // Extract unique departments for filter dropdown
  const departments = Array.from(new Set(history.map((item) => item.department).filter(Boolean)));

  const filtered = history.filter((item) => {
    const q = search.toLowerCase().trim();
    const matchesSearch =
      !q ||
      item.candidate_name.toLowerCase().includes(q) ||
      item.position_title.toLowerCase().includes(q) ||
      (item.referred_by_name && item.referred_by_name.toLowerCase().includes(q)) ||
      item.referral_number.toLowerCase().includes(q) ||
      item.department.toLowerCase().includes(q);

    const matchesDept = departmentFilter === 'ALL' || item.department === departmentFilter;

    return matchesSearch && matchesDept;
  });

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Header Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '28px',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'rgba(16, 185, 129, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10b981',
              }}
            >
              <Award size={20} />
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              Hired History
            </h2>
          </div>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
            Official record of candidates successfully hired for specific Tangentia requisitions.
          </p>
        </div>

        {/* Quick summary stats & actions */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div
            style={{
              padding: '10px 18px',
              borderRadius: '10px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#10b981' }}>
              {history.length}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Total Hires
            </div>
          </div>
          <div
            style={{
              padding: '10px 18px',
              borderRadius: '10px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {departments.length}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Departments
            </div>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleExportExcel}
            disabled={isExporting || history.length === 0}
            title="Download Hired Referral History in Microsoft Excel (.xlsx)"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', height: '42px', padding: '0 16px' }}
          >
            <FileSpreadsheet size={16} color="#10b981" />
            <span>{isExporting ? 'Exporting...' : 'Export to Excel'}</span>
          </button>
        </div>

      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '24px',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <div style={{ position: 'relative', flex: '1 1 300px' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '14px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
          <input
            type="text"
            placeholder="Search by candidate, position, referrer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 14px 10px 40px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '0.88rem',
              outline: 'none',
            }}
          />
        </div>

        {departments.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color="var(--text-muted)" />
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                fontSize: '0.88rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">All Departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading hired referral history...
        </div>
      ) : filtered.length === 0 ? (
        <div
          style={{
            padding: '60px 20px',
            textAlign: 'center',
            background: 'var(--bg-secondary)',
            borderRadius: '12px',
            border: '1px dashed var(--border-subtle)',
          }}
        >
          <Award size={40} color="var(--text-muted)" style={{ opacity: 0.5, marginBottom: '12px' }} />
          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            {search || departmentFilter !== 'ALL' ? 'No matching hired records found' : 'No Hired Candidates Yet'}
          </h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            {search || departmentFilter !== 'ALL'
              ? 'Try adjusting your search terms or department filter.'
              : 'When a candidate referral status is transitioned to "Hired", the position and candidate record will appear here.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filtered.map((item) => (
            <div
              key={item.id}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '12px',
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                transition: 'all 0.15s ease',
              }}
            >
              {/* Left Column: Job Position & Department Details */}
              <div style={{ flex: '1 1 360px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      color: '#10b981',
                      background: 'rgba(16, 185, 129, 0.12)',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <CheckCircle2 size={12} /> Hired & Position Closed
                  </span>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      color: 'var(--text-muted)',
                      background: 'var(--bg-main)',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    {item.referral_number}
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: '1.12rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px',
                  }}
                >
                  {item.position_title}
                </h3>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    fontSize: '0.82rem',
                    color: 'var(--text-secondary)',
                    flexWrap: 'wrap',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Building size={14} color="var(--text-muted)" />
                    {item.department}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <MapPin size={14} color="var(--text-muted)" />
                    {item.location}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Briefcase size={14} color="var(--text-muted)" />
                    {item.employment_type || 'Full-time'}
                  </span>
                </div>
              </div>

              {/* Middle Column: Hired Candidate Name */}
              <div
                style={{
                  flex: '0 1 240px',
                  padding: '12px 18px',
                  background: 'var(--bg-main)',
                  borderRadius: '10px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Hired Candidate
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <UserCheck size={16} color="#10b981" />
                  {item.candidate_name}
                </div>
              </div>

              {/* Right Column: Referrer & Hire Date */}
              <div style={{ flex: '0 1 200px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Referred By: </span>
                  <span style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {item.referred_by_name || 'Anonymous Employee'}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <Calendar size={13} />
                  <span>Hired on {formatDate(item.hired_at)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
