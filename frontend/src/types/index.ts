export type OpportunityCategory =
  | 'referrals'
  | 'internships'
  | 'fresher_jobs'
  | 'hackathons'
  | 'scholarships'
  | 'courses'
  | 'research';

export type TrackingStatus =
  | 'NEW'
  | 'REVIEWED'
  | 'INTERESTED'
  | 'CONNECTION_PENDING'
  | 'CONNECTED'
  | 'REPLY_RECEIVED'
  | 'REFERRAL_RECEIVED'
  | 'APPLICATION_READY'
  | 'APPLIED'
  | 'INTERVIEW'
  | 'REJECTED'
  | 'CLOSED'
  | 'EXPIRED'
  | 'DISMISSED';

export interface Skill {
  id?: number;
  name: string;
  category: string;
  proficiency: string;
}

export interface Project {
  id?: number;
  title: string;
  achievement?: string | null;
  description?: string | null;
  tech_stack: string[];
  url?: string | null;
}

export interface UserProfile {
  id: number;
  full_name: string;
  education: string;
  institution: string;
  location: string;
  graduation_year: number;
  current_status: string;
  target_career_positioning: string;
  career_goal: string;
  career_interests: string[];
  preferred_locations: string[];
  cgpa?: number | null;
  resume_summary?: string | null;
  skills: Skill[];
  projects: Project[];
  updated_at: string;
}

export interface OpportunityScore {
  overall_score: number;
  skill_score: number;
  eligibility_score: number;
  relevance_score: number;
  location_score: number;
  referral_freshness_score: number;
  explanation: string;
  recommended_action: string;
  scoring_model: string;
  scored_at: string;
}

export interface EligibilityAssessment {
  status: string;
  matched_requirements: string[];
  missing_requirements: string[];
  disqualifying_requirements: string[];
  verification_questions: string[];
  summary: string;
  assessed_at: string;
}

export interface OpportunityEvidence {
  id: number;
  evidence_type: string;
  source_url: string;
  excerpt: string;
  author_name?: string | null;
  extracted_at: string;
}

export interface MessageDraft {
  id: number;
  opportunity_id: number;
  draft_type: string;
  subject?: string | null;
  body: string;
  created_at: string;
}

export interface OpportunityStatusHistory {
  id: number;
  from_status?: string | null;
  to_status: string;
  note?: string | null;
  changed_at: string;
}

export interface OpportunitySummary {
  id: number;
  title: string;
  organization: string;
  category: OpportunityCategory;
  subcategory?: string | null;
  description: string;
  location: string;
  is_remote: boolean;
  is_hybrid: boolean;
  deadline?: string | null;
  discovered_at: string;
  last_verified_at?: string | null;
  active_status: string;
  verification_status: string;
  opportunity_type?: string | null;
  application_status?: string | null;
  source_url: string;
  application_url?: string | null;
  referral_classification?: string | null;
  referral_confidence?: number | null;
  required_skills: string[];
  preferred_skills: string[];
  compensation_or_stipend?: string | null;
  ai_status: string;
  tracking_status: TrackingStatus;
  is_interested: boolean;
  follow_up_date?: string | null;
  next_action?: string | null;
  score?: OpportunityScore | null;
  eligibility?: EligibilityAssessment | null;
}

export interface OpportunityDetail extends OpportunitySummary {
  canonical_url: string;
  referral_instructions?: string | null;
  education_requirement?: string | null;
  graduation_year_requirement?: string | null;
  experience_requirement?: string | null;
  duration?: string | null;
  extra_metadata: Record<string, unknown>;
  personal_notes?: string | null;
  application_date?: string | null;
  referral_received_date?: string | null;
  evidences: OpportunityEvidence[];
  drafts: MessageDraft[];
  status_history: OpportunityStatusHistory[];
}

export interface PaginatedOpportunities {
  items: OpportunitySummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FollowUp {
  id: number;
  opportunity_id: number;
  due_date: string;
  status: string;
  notes?: string | null;
  completed_at?: string | null;
  created_at: string;
  opportunity_title?: string | null;
  organization?: string | null;
}

export interface Application {
  id: number;
  opportunity_id: number;
  status: string;
  portal_url?: string | null;
  applied_at?: string | null;
  resume_version?: string | null;
  notes?: string | null;
  created_at: string;
  opportunity_title?: string | null;
  organization?: string | null;
}

export interface DiscoverySource {
  id: number;
  name: string;
  adapter_key: string;
  source_type: string;
  enabled: boolean;
  frequency_hours: number;
  config_json: Record<string, unknown>;
  last_run_at?: string | null;
  last_status?: string | null;
  last_error?: string | null;
  records_retrieved?: number;
  valid_records?: number;
  duplicate_records?: number;
  new_records?: number;
  avg_response_time_ms?: number;
}

export interface DiscoveryRun {
  id: number;
  started_at: string;
  finished_at?: string | null;
  status: string;
  trigger_type: string;
  sources_checked: number;
  sources_failed: number;
  opportunities_discovered: number;
  new_opportunities: number;
  high_match_count: number;
  errors_json: Array<{ source: string; error: string }>;
  summary_text?: string | null;
}

export interface DashboardSummary {
  new_opportunities: number;
  high_match_opportunities: number;
  referrals_in_progress: number;
  applications_submitted: number;
  replies_received: number;
  upcoming_deadlines: number;
  follow_ups_due: number;
  total_opportunities: number;
  active_vacancies?: number;
  research_papers?: number;
  closed_opportunities?: number;
  latest_run?: DiscoveryRun | null;
}

export interface AnalyticsSeriesPoint {
  label: string;
  count: number;
}

export interface DashboardAnalytics {
  discovered_over_time: AnalyticsSeriesPoint[];
  by_category: AnalyticsSeriesPoint[];
  application_pipeline: AnalyticsSeriesPoint[];
  score_distribution: AnalyticsSeriesPoint[];
  outreach_status: AnalyticsSeriesPoint[];
  by_opportunity_type?: AnalyticsSeriesPoint[];
  by_application_status?: AnalyticsSeriesPoint[];
}

export interface ReplyAnalyzeResponse {
  classification: string;
  explanation: string;
  recommended_next_step: string;
  suggested_response: string;
  suggested_follow_up_date?: string | null;
}

