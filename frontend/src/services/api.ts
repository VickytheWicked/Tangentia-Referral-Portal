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
} from '../types';

const API_BASE = 'http://localhost:8000/api';

// Current active dev role stored in localStorage for seamless dev mode testing
let currentDevRole: UserRole = (localStorage.getItem('dev_role') as UserRole) || 'employee';
let currentAuthToken: string | null = localStorage.getItem('msal_token');

export const setDevRole = (role: UserRole) => {
  currentDevRole = role;
  localStorage.setItem('dev_role', role);
};

export const getStoredDevRole = (): UserRole => currentDevRole;

export const setAuthToken = (token: string | null) => {
  currentAuthToken = token;
  if (token) {
    localStorage.setItem('msal_token', token);
  } else {
    localStorage.removeItem('msal_token');
  }
};

const getHeaders = (isMultipart: boolean = false): HeadersInit => {
  const headers: Record<string, string> = {
    'X-Dev-Role': currentDevRole,
  };

  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`;
  } else {
    // Default dev token for dev mode
    headers['Authorization'] = `Bearer dev-${currentDevRole === 'hr_admin' ? 'hr' : 'employee'}-token`;
  }

  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }

  return headers;
};

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
  async getAuthConfig() {
    const res = await fetch(`${API_BASE}/auth/config`);
    return handleResponse<{ tenant_id: string; client_id: string; authority: string; dev_mode: boolean }>(res);
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

  // Submit Referral
  async submitReferral(formData: FormData): Promise<ReferralSummary> {
    const res = await fetch(`${API_BASE}/referrals`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
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
      throw new Error('Failed to retrieve CV file.');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = suggestedFilename || `CV_${referralId}.pdf`;
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
};
