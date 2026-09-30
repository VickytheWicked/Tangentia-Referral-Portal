import {
  User,
  JobPosition,
  ReferralSummary,
  ReferralDetail,
  StatusHistory,
  HRNote,
  DuplicateCheckResponse,
  AnalyticsResponse,
  UserRole,
  SyncCatsResponse,
  HiredHistoryItem,
  CVExtractionPreview,
} from '../types';
import {
  OpeningSuggestions,
  CandidateProfileDetail,
  CVIntelligenceStatus,
} from '../types/cv_intelligence';
import { HistoricalSuggestionsResponse } from '../types/historical_suggestions';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').replace(/\/+$/, '');

// Clear any legacy persistent tokens from localStorage to prevent accidental auto-login
// try {
//   localStorage.removeItem('tangentia_auth_token');
//   localStorage.removeItem('dev_role');
// } catch {}

// Auth token stored in sessionStorage for the active HR Administrator tab session
let currentAuthToken: string | null = sessionStorage.getItem('tangentia_auth_token');
let currentDevRole: UserRole = (sessionStorage.getItem('dev_role') as UserRole) || 'employee';

export const setDevRole = (role: UserRole) => {
  currentDevRole = role;
  sessionStorage.setItem('dev_role', role);
};

export const getStoredDevRole = (): UserRole => currentDevRole;

export const setAuthToken = (token: string | null) => {
  currentAuthToken = token;
  if (token) {
    sessionStorage.setItem('tangentia_auth_token', token);
  } else {
    sessionStorage.removeItem('tangentia_auth_token');
    try {
      localStorage.removeItem('tangentia_auth_token');
    } catch { }
  }
};

export const getAuthToken = (): string | null => currentAuthToken;

const getHeaders = (isMultipart: boolean = false): HeadersInit => {
  const headers: Record<string, string> = {};

  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`;
  }

  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }

  return headers;
};

// Resilient fetch wrapper with customizable timeout (default 25s, extended for AI extraction & uploads)
interface CustomRequestInit extends RequestInit {
  timeoutMs?: number;
}

const fetchWithTimeout = async (input: RequestInfo | URL, init?: CustomRequestInit): Promise<Response> => {
  const timeoutMs = init?.timeoutMs || 25000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await window.fetch(input, {
      ...init,
      signal: init?.signal || controller.signal,
    });
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new Error(`Network request timed out (${Math.round(timeoutMs / 1000)}s). Please check your connection and try again.`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
};

const fetch = fetchWithTimeout;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'An unexpected error occurred';
    try {
      const json = await res.json();
      errorDetail = json.detail || JSON.stringify(json);
    } catch {
      errorDetail = await res.text() || res.statusText;
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Auth
  async login(credentials: { email: string; password: string }): Promise<{ access_token: string; token_type: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    return handleResponse<{ access_token: string; token_type: string; user: User }>(res);
  },

  async getAuthConfig() {
    const res = await fetch(`${API_BASE}/auth/config`);
    return handleResponse<{ dev_mode: boolean; auth_domain: string }>(res);
  },

  async getCurrentUser(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders(),
    });
    return handleResponse<User>(res);
  },

  // Job Openings
  async getJobs(includeInactive: boolean = false): Promise<JobPosition[]> {
    const res = await fetch(`${API_BASE}/jobs?include_inactive=${includeInactive}`, {
      headers: getHeaders(),
    });
    return handleResponse<JobPosition[]>(res);
  },

  async getJob(id: string): Promise<JobPosition> {
    const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(id)}`, {
      headers: getHeaders(),
    });
    return handleResponse<JobPosition>(res);
  },

  async createJob(data: Partial<JobPosition>): Promise<JobPosition> {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse<JobPosition>(res);
  },

  async updateJob(id: string, data: Partial<JobPosition>): Promise<JobPosition> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse<JobPosition>(res);
  },

  async syncCatsJobs(deactivateMissing: boolean = true): Promise<SyncCatsResponse> {
    const res = await fetch(`${API_BASE}/jobs/sync-cats?deactivate_missing=${deactivateMissing}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse<SyncCatsResponse>(res);
  },

  async previewCatsJobs(): Promise<{ total_found: number; jobs: any[] }> {
    const res = await fetch(`${API_BASE}/jobs/sync-cats/preview`, {
      headers: getHeaders(),
    });
    return handleResponse<{ total_found: number; jobs: any[] }>(res);
  },

  // Duplicate Check
  async checkDuplicate(data: {
    candidate_email: string;
    candidate_phone: string;
    candidate_name: string;
    position_id: string;
  }): Promise<DuplicateCheckResponse> {
    const res = await fetch(`${API_BASE}/referrals/check-duplicate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse<DuplicateCheckResponse>(res);
  },

  // Extract CV Details for Autofill (allows up to 60s for AI processing and model fallbacks)
  async extractCV(file: File): Promise<CVExtractionPreview> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/referrals/extract-cv`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
      timeoutMs: 60000,
    });
    return handleResponse<CVExtractionPreview>(res);
  },

  // Submit Referral (allows up to 60s for cloud storage upload, Excel sync, and validation)
  async submitReferral(formData: FormData): Promise<ReferralSummary> {
    const res = await fetch(`${API_BASE}/referrals`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
      timeoutMs: 60000,
    });
    return handleResponse<ReferralSummary>(res);
  },

  // Referrals
  async getMyReferrals(): Promise<ReferralSummary[]> {
    const res = await fetch(`${API_BASE}/referrals`, {
      headers: getHeaders(),
    });
    return handleResponse<ReferralSummary[]>(res);
  },

  async getHiredHistory(positionId?: string): Promise<HiredHistoryItem[]> {
    const url = positionId
      ? `${API_BASE}/referrals/hired-history?position_id=${encodeURIComponent(positionId)}`
      : `${API_BASE}/referrals/hired-history`;
    const res = await fetch(url, {
      headers: getHeaders(),
    });
    return handleResponse<HiredHistoryItem[]>(res);
  },

  async downloadHiredHistoryExcel(positionId?: string): Promise<void> {
    const url = positionId
      ? `${API_BASE}/referrals/hired-history/excel-export?position_id=${encodeURIComponent(positionId)}`
      : `${API_BASE}/referrals/hired-history/excel-export`;
    const res = await fetch(url, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      throw new Error('Failed to export Hired Referral History Excel spreadsheet.');
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = 'Tangentia_Hired_History.xlsx';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(blobUrl);
    document.body.removeChild(a);
  },

  async getReferralDetail(id: string): Promise<ReferralDetail> {

    const res = await fetch(`${API_BASE}/referrals/${id}`, {
      headers: getHeaders(),
    });
    return handleResponse<ReferralDetail>(res);
  },

  async withdrawReferral(id: string, comment?: string): Promise<ReferralSummary> {
    const res = await fetch(`${API_BASE}/referrals/${id}/withdraw`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ comment }),
    });
    return handleResponse<ReferralSummary>(res);
  },

  // CV Download
  async downloadCV(referralId: string, suggestedFilename?: string): Promise<void> {
    const res = await fetch(`${API_BASE}/referrals/${referralId}/cv`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      let errMsg = 'Failed to retrieve CV file.';
      try {
        const errorData = await res.json();
        if (errorData && errorData.detail) {
          errMsg = errorData.detail;
        }
      } catch {
        // Fallback to generic message
      }
      throw new Error(errMsg);
    }

    let filename = suggestedFilename;
    const disposition = res.headers.get('Content-Disposition');
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) {
        filename = match[1].trim();
      }
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `CV_${referralId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  // Excel Export
  async downloadExcelExport(): Promise<void> {
    const res = await fetch(`${API_BASE}/hr/referrals/excel-export`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      throw new Error('Failed to export Microsoft Excel workbook.');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Tangentia_Referrals.xlsx';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  async getStatusHistory(id: string): Promise<StatusHistory[]> {
    const res = await fetch(`${API_BASE}/referrals/${id}/status-history`, {
      headers: getHeaders(),
    });
    return handleResponse<StatusHistory[]>(res);
  },

  // HR Endpoints
  async getAllReferrals(params: {
    status?: string;
    position_id?: string;
    department?: string;
    search?: string;
  } = {}): Promise<ReferralSummary[]> {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.position_id) query.append('position_id', params.position_id);
    if (params.department) query.append('department', params.department);
    if (params.search) query.append('search', params.search);

    const res = await fetch(`${API_BASE}/hr/referrals?${query.toString()}`, {
      headers: getHeaders(),
    });
    return handleResponse<ReferralSummary[]>(res);
  },

  async updateStatus(referralId: string, status: string, comment?: string): Promise<ReferralSummary> {
    const res = await fetch(`${API_BASE}/hr/referrals/${referralId}/status`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ status, comment }),
    });
    return handleResponse<ReferralSummary>(res);
  },

  async archiveReferral(referralId: string, comment?: string): Promise<ReferralSummary> {
    const query = comment ? `?comment=${encodeURIComponent(comment)}` : '';
    const res = await fetch(`${API_BASE}/hr/referrals/${referralId}/archive${query}`, {
      method: 'PUT',
      headers: getHeaders(),
    });
    return handleResponse<ReferralSummary>(res);
  },

  async deleteReferral(referralId: string): Promise<{ message: string; id: string }> {
    const res = await fetch(`${API_BASE}/hr/referrals/${referralId}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return handleResponse<{ message: string; id: string }>(res);
  },

  async addHRNote(referralId: string, note: string): Promise<HRNote> {
    const res = await fetch(`${API_BASE}/hr/referrals/${referralId}/notes`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ note }),
    });
    return handleResponse<HRNote>(res);
  },

  async getHRNotes(referralId: string): Promise<HRNote[]> {
    const res = await fetch(`${API_BASE}/hr/referrals/${referralId}/notes`, {
      headers: getHeaders(),
    });
    return handleResponse<HRNote[]>(res);
  },

  async getAnalytics(): Promise<AnalyticsResponse> {
    const res = await fetch(`${API_BASE}/hr/analytics`, {
      headers: getHeaders(),
    });
    return handleResponse<AnalyticsResponse>(res);
  },

  // ================================================================
  // CV Intelligence & HR Suggestions Endpoints
  // ================================================================
  async getCVIntelligenceStatus(): Promise<CVIntelligenceStatus> {
    const res = await fetch(`${API_BASE}/cv-intelligence/status`, {
      headers: getHeaders(),
    });
    return handleResponse<CVIntelligenceStatus>(res);
  },

  async getHRSuggestions(): Promise<OpeningSuggestions[]> {
    const res = await fetch(`${API_BASE}/cv-intelligence/suggestions`, {
      headers: getHeaders(),
    });
    return handleResponse<OpeningSuggestions[]>(res);
  },

  async getCandidateIntelligence(referralId: string): Promise<CandidateProfileDetail> {
    const res = await fetch(`${API_BASE}/cv-intelligence/candidates/${referralId}`, {
      headers: getHeaders(),
    });
    return handleResponse<CandidateProfileDetail>(res);
  },

  async processCandidateCV(referralId: string, force: boolean = false): Promise<CandidateProfileDetail> {
    const res = await fetch(`${API_BASE}/cv-intelligence/process/${referralId}?force=${force}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse<CandidateProfileDetail>(res);
  },

  async processOpeningCVs(positionId: string): Promise<{ status: string; candidate_count: number; message: string }> {
    const res = await fetch(`${API_BASE}/cv-intelligence/process-opening/${positionId}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse<{ status: string; candidate_count: number; message: string }>(res);
  },

  // ================================================================
  // Historical Referral Suggestions (Isolated & Local-Only)
  // ================================================================
  async getHistoricalSuggestions(positionId: string, threshold?: number): Promise<HistoricalSuggestionsResponse> {
    const query = threshold !== undefined ? `?threshold=${threshold}` : '';
    const res = await fetch(`${API_BASE}/historical-suggestions/positions/${positionId}${query}`, {
      headers: getHeaders(),
    });
    return handleResponse<HistoricalSuggestionsResponse>(res);
  },
};

export const apiService = api;
