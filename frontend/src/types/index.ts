export type UserRole = 'employee' | 'hr_admin';

export type ReferralStatusType = 
  | 'Submitted'
  | 'Under Review'
  | 'Shortlisted'
  | 'Interview'
  | 'Selected'
  | 'Hired'
  | 'Rejected'
  | 'Withdrawn'
  | 'Archived';

export interface User {
  id: string;
  entra_user_id: string;
  name: string;
  email: string;
  role: UserRole;
  department?: string;
  created_at: string;
}

export interface JobPosition {
  id: string;
  title: string;
  department: string;
  description: string;
  location: string;
  employment_type: string;
  is_active: boolean;
  created_at: string;
}

export interface SyncCatsResponse {
  success: boolean;
  message: string;
  total_scraped: number;
  created_count: number;
  updated_count: number;
  deactivated_count: number;
  jobs: JobPosition[];
}


export interface StatusHistory {
  id: string;
  referral_id: string;
  old_status?: string | null;
  new_status: ReferralStatusType;
  changed_by_user_id: string;
  changed_by_name?: string;
  comment?: string | null;
  created_at: string;
}

export interface HRNote {
  id: string;
  referral_id: string;
  created_by_user_id: string;
  created_by_name?: string;
  note: string;
  created_at: string;
  updated_at: string;
}

export interface ReferralSummary {
  id: string;
  referral_number: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone: string;
  years_of_experience: number;
  relationship: string;
  status: ReferralStatusType;
  position_id: string;
  position_title: string;
  position_department: string;
  referred_by_id: string;
  referred_by_name: string;
  referred_by_email: string;
  original_filename: string;
  created_at: string;
  updated_at: string;
}

export interface ReferralDetail extends ReferralSummary {
  linkedin_url?: string | null;
  github_url?: string | null;
  referral_note: string;
  candidate_consent: boolean;
  position?: JobPosition;
  status_history: StatusHistory[];
  hr_notes: HRNote[];
}

export interface DuplicateMatch {
  referral_id: string;
  referral_number: string;
  candidate_name: string;
  candidate_email: string;
  position_title: string;
  status: string;
  referred_by_name: string;
  created_at: string;
  match_reason: string;
}

export interface DuplicateCheckResponse {
  is_duplicate: boolean;
  matches: DuplicateMatch[];
}

export interface StatusFunnelStep {
  status: string;
  count: number;
  percentage: number;
}

export interface DepartmentMetric {
  department: string;
  total_referrals: number;
  hired_count: number;
}

export interface MonthlyTrend {
  month: string;
  count: number;
}

export interface TopReferrer {
  user_id: string;
  user_name: string;
  user_email: string;
  referral_count: number;
  hired_count: number;
}

export interface AnalyticsResponse {
  total_referrals: number;
  active_referrals: number;
  hired_referrals: number;
  rejected_referrals: number;
  withdrawn_referrals: number;
  funnel: StatusFunnelStep[];
  by_department: DepartmentMetric[];
  monthly_trends: MonthlyTrend[];
  top_referrers: TopReferrer[];
}

export interface HiredHistoryItem {
  id: string;
  referral_number: string;
  candidate_name: string;
  position_id: string;
  position_title: string;
  department: string;
  location: string;
  employment_type?: string;
  referred_by_name?: string;
  hired_at: string;
  status: string;
}
