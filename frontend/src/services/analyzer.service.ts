import { apiClient } from './api';

export interface PredictDomainResponse {
  predicted_domain: string;
  confidence: number;
  probabilities: Record<string, number>;
  top_domains: Array<{ domain: string; confidence: number }>;
}

export interface GapItem {
  id: string;
  name: string;
  severity: string;
  rationale: string;
}

export interface FollowUpQuestionItem {
  ingredient_id: string;
  name: string;
  severity: string;
  question: string;
  rationale: string;
}

export interface GapDetectionResponse {
  domain: string;
  total_ingredients: number;
  provided_count: number;
  missing_count: number;
  completeness_ratio: number;
  provided_ingredients: GapItem[];
  missing_ingredients: GapItem[];
  follow_up_questions: FollowUpQuestionItem[];
}

export interface InformationQualityScores {
  statutory_grounding: number;
  factual_completeness: number;
  citation_validity: number;
  contradiction_penalty: number;
}

export interface InformationQualityResponse {
  score: number;
  badge: 'COMPREHENSIVE_QUALITY' | 'MODERATE_QUALITY_GAPS' | 'LOW_QUALITY_INCOMPLETE';
  badge_color: string;
  summary: string;
  component_scores: InformationQualityScores;
}

export interface ApplicableStatute {
  act_code: string;
  act_title: string;
  section_number: string;
  section_title: string;
  chapter?: string;
  provision_type?: string;
  source_url?: string;
  document: string;
  distance?: number;
  historical_crosswalk?: Record<string, any>;
}

export interface SituationAnalysisResponse {
  narrative: string;
  predicted_domain: string;
  classification_confidence: number;
  top_candidate_domains: Array<{ domain: string; confidence: number }>;
  applicable_statutes: ApplicableStatute[];
  temporal_applicability?: Record<string, any>;
  legal_gaps: GapDetectionResponse;
  citation_verification: Record<string, any>;
  uncertainty_analysis?: Record<string, any>;
  statute_element_mapping?: StatuteExplanationResponse;
  information_quality: InformationQualityResponse;
  recommended_actions: Array<{ step: string; action: string }>;
  emergency_helplines: Record<string, string>;
  statutory_disclaimer: string;
}

export interface StatuteElementItem {
  id: string;
  label: string;
  statutory_text: string;
  fulfilled: boolean;
  evidence_excerpt?: string | null;
  explanation: string;
}

export interface StatuteExplanationResponse {
  act_code: string;
  section_number: string;
  offence_title: string;
  total_elements: number;
  fulfilled_elements: number;
  unfulfilled_elements: number;
  fulfillment_ratio: number;
  elements_breakdown: StatuteElementItem[];
}

export interface ResolveGapsResponse {
  augmented_narrative: string;
  previous_score: number;
  elevated_score: number;
  score_delta: number;
  resolved_count: number;
  remaining_count: number;
  upgraded_badge: string;
  upgraded_badge_color: string;
  updated_analysis: SituationAnalysisResponse;
  statute_explanation?: StatuteExplanationResponse | null;
}

export interface GroundedAiGuidanceResponse {
  domain: string;
  information_quality: InformationQualityResponse;
  grounded_ai_guidance: {
    source: string;
    plain_language_summary: string;
    citizen_rights: string[];
    immediate_steps: string[];
    advisory_warning: string;
    statutory_disclaimer: string;
  };
}

export interface ModelMetricsResponse {
  n_samples: number;
  n_classes: number;
  classes: string[];
  cv_splits: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  weighted_f1: number;
  fold_f1_scores: number[];
  confusion_matrix: number[][];
  dataset_limitations: string[];
}

export const analyzerService = {
  async predictDomain(narrative: string): Promise<PredictDomainResponse> {
    const response = await apiClient.post<PredictDomainResponse>('/analyzer/predict-domain', { narrative });
    return response.data;
  },

  async analyzeSituation(payload: {
    narrative: string;
    incident_date?: string;
    is_continuing_offense?: boolean;
    preferred_language?: string;
  }): Promise<SituationAnalysisResponse> {
    const response = await apiClient.post<SituationAnalysisResponse>('/analyzer/analyze-situation', payload);
    return response.data;
  },

  async detectGaps(narrative: string, domain?: string): Promise<GapDetectionResponse> {
    const response = await apiClient.post<GapDetectionResponse>('/analyzer/detect-gaps', { narrative, domain });
    return response.data;
  },

  async explainStatute(payload: {
    narrative: string;
    act_code: string;
    section_number: string;
  }): Promise<StatuteExplanationResponse> {
    const response = await apiClient.post<StatuteExplanationResponse>('/analyzer/explain-statute', payload);
    return response.data;
  },

  async resolveGaps(payload: {
    original_narrative: string;
    domain: string;
    incident_date?: string;
    is_continuing_offense?: boolean;
    preferred_language?: string;
    answers: Record<string, string>;
  }): Promise<ResolveGapsResponse> {
    const response = await apiClient.post<ResolveGapsResponse>('/analyzer/resolve-gaps', payload);
    return response.data;
  },

  async generateAiExplanation(payload: {
    narrative: string;
    incident_date?: string;
    is_continuing_offense?: boolean;
    preferred_language?: string;
  }): Promise<GroundedAiGuidanceResponse> {
    const response = await apiClient.post<GroundedAiGuidanceResponse>('/analyzer/generate-ai-explanation', payload);
    return response.data;
  },

  async getModelMetrics(): Promise<ModelMetricsResponse> {
    const response = await apiClient.get<ModelMetricsResponse>('/analyzer/model-metrics');
    return response.data;
  },
};
