export type ExtractionStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export type MatchLevel = 'Strong Match' | 'Good Match' | 'Potential Match';

export type RequirementStatus =
  | 'SUPPORTED'
  | 'NOT_MET'
  | 'NOT_DEMONSTRATED'
  | 'PARTIALLY_SUPPORTED';

export type RequirementCategory =
  | 'MANDATORY'
  | 'REQUIRED_EXPERIENCE'
  | 'REQUIRED_SKILLS'
  | 'REQUIRED_DOMAIN'
  | 'REQUIRED_FRAMEWORKS'
  | 'REQUIRED_ARCHITECTURE'
  | 'PREFERRED'
  | 'OTHER';

export interface RequirementAnalysisItem {
  requirement: string;
  category: RequirementCategory;
  required_value: string;
  status: RequirementStatus;
  cv_evidence: string;
  reasoning: string;
}

export interface OverallAnalysis {
  key_observations: string[];
  mandatory_requirements: RequirementAnalysisItem[];
  supported_requirements: RequirementAnalysisItem[];
  partially_supported_requirements: RequirementAnalysisItem[];
  not_demonstrated_requirements: RequirementAnalysisItem[];
  analyzed_at?: string;
}

export interface EducationItem {
  degree?: string;
  institution?: string;
  graduation_year?: string;
  field_of_study?: string;
  grade_or_score?: string;
}

export interface ExperienceItem {
  company?: string;
  job_title?: string;
  duration?: string;
  responsibilities?: string[];
}

export interface ProjectItem {
  name?: string;
  description?: string;
  technologies?: string[];
}

export interface CertificationItem {
  name?: string;
  issuer?: string;
  year?: string;
}

export interface JobMatchItem {
  id: string;
  position_id: string;
  match_level: string;
  matched_skills: string[];
  missing_skills: string[];
  experience_match?: string;
  explanation: string[];
  fit_summary?: string;
  requirement_analysis?: OverallAnalysis; // New evidence-based analysis
}

export interface SuggestedCandidateSummary {
  referral_id: string;
  candidate_name: string;
  candidate_email: string;
  original_filename: string;
  extraction_status: ExtractionStatus;
  match_level?: string;
  years_of_experience: number;
  matched_skills: string[];
  missing_skills: string[];
  explanation: string[];
  fit_summary?: string;
  referral_status: string;
  referred_at: string;
  priority_score?: number;
}

export interface OpeningSuggestions {
  position_id: string;
  title: string;
  department: string;
  location: string;
  employment_type: string;
  description?: string;
  expected_skills: string[];
  min_experience_years: number;
  selection_criteria?: string[];
  key_qualities?: string[];
  hiring_guidance?: string;
  strong_matches: SuggestedCandidateSummary[];
  good_matches: SuggestedCandidateSummary[];
  potential_matches: SuggestedCandidateSummary[];
  pending_extraction: SuggestedCandidateSummary[];
  failed_extraction: SuggestedCandidateSummary[];
  total_candidates: number;
}

export interface CandidateProfileDetail {
  id?: string;
  referral_id: string;
  referral_number?: string;
  candidate_name?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  years_of_experience: number;
  skills: string[];
  education: EducationItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  certifications: CertificationItem[];
  extraction_status: ExtractionStatus;
  extraction_error?: string;
  extracted_at?: string;
  match?: JobMatchItem;
  original_filename: string;
  position_title: string;
  position_id: string;
  referral_status: string;
  referred_by_name?: string;
  referred_by_email?: string;
  relationship?: string;
  referral_note?: string;
  created_at?: string;
}

export interface CVIntelligenceStatus {
  enabled: boolean;
  provider: string;
  model: string;
  has_api_key: boolean;
}
