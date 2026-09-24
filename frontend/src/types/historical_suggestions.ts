import { EducationItem, ExperienceItem, ProjectItem, CertificationItem } from './cv_intelligence';

export type HistoricalRelevanceCategory = 'Strong Relevance' | 'Good Relevance' | 'Potential Relevance';

export interface HistoricalCandidateItem {
  referral_id: string;
  referral_number: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string;
  
  // Original Provenance
  original_position_id: string;
  original_position_title: string;
  original_referral_date?: string;
  referred_by_name: string;
  original_status: string; // "Archived"
  
  // Relevance
  relevance_category: HistoricalRelevanceCategory;
  relevance_score: number;
  matched_skills: string[];
  missing_skills: string[];
  experience_summary: string;
  relevance_reasons: string[];
  fit_narrative?: string;
  
  // Candidate Profile
  years_of_experience: number;
  skills: string[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  education: EducationItem[];
  certifications: CertificationItem[];
  
  original_filename: string;
}

export interface HistoricalSuggestionsResponse {
  current_position_id: string;
  current_position_title: string;
  threshold_applied: number;
  total_archived_evaluated: number;
  total_relevant_found: number;
  suggestions: HistoricalCandidateItem[];
}
