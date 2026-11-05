import { apiClient } from './api';

export interface ExtractedEntityDate {
  iso_date: string;
  raw_text: string;
  page_number: number;
  confidence: number;
}

export interface ExtractedEntityAmount {
  amount: number;
  currency: string;
  formatted: string;
  raw_text: string;
  page_number: number;
  confidence: number;
}

export interface ExtractedEntityIdentifier {
  type: string;
  value: string;
  raw_text: string;
  page_number: number;
  confidence: number;
}

export interface ExtractedEntityParty {
  type: string;
  value: string;
  raw_text: string;
  page_number: number;
  confidence: number;
}

export interface ExtractedEntityEvent {
  event_type: string;
  title: string;
  date: string;
  evidence_snippet: string;
  page_number: number;
  confidence: string;
}

export interface ExtractedEntities {
  document_filename?: string;
  dates: ExtractedEntityDate[];
  monetary_amounts: ExtractedEntityAmount[];
  identifiers: ExtractedEntityIdentifier[];
  parties: ExtractedEntityParty[];
  events: ExtractedEntityEvent[];
  total_entities_found?: number;
}

export interface EvidenceDocument {
  document_id: number;
  case_id: number;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash?: string;
  category: string;
  category_title: string;
  classification_confidence: number;
  total_pages?: number;
  is_scanned?: boolean;
  ocr_performed?: boolean;
  is_processed?: boolean;
  extracted_entities: ExtractedEntities;
  extracted_text_preview: string;
  ocr_extracted_text?: string;
  created_at?: string;
}

export interface TimelineEvent {
  id: number;
  case_id: number;
  evidence_id?: number | null;
  event_date: string;
  event_title: string;
  event_description: string;
  source_reference?: string;
  confidence_level: string;
  sequence_number?: number;
  is_manual?: boolean;
}

export interface TemporalWarning {
  type: string;
  gap_days: number;
  from_event: string;
  to_event: string;
  advisory: string;
}

export interface CaseTimeline {
  case_id: number;
  total_events: number;
  dated_events_count: number;
  undated_events_count: number;
  earliest_date?: string | null;
  latest_date?: string | null;
  chronological_events: TimelineEvent[];
  undated_events: TimelineEvent[];
  temporal_warnings: TemporalWarning[];
}

export interface EvidenceDiscrepancy {
  type: string;
  severity: 'HIGH' | 'MODERATE' | 'LOW';
  description: string;
  affected_documents: string[];
}

export interface DocumentaryGap {
  missing_document_type: string;
  title: string;
  statutory_rationale: string;
}

export interface ConsistencyCheckResponse {
  case_id: number;
  is_consistent: boolean;
  discrepancies_count: number;
  discrepancies: EvidenceDiscrepancy[];
  documentary_gaps_count: number;
  documentary_gaps: DocumentaryGap[];
  summary: string;
}

export const evidenceService = {
  async uploadEvidence(caseId: number, files: File[]): Promise<EvidenceDocument[]> {
    const formData = new FormData();
    formData.append('case_id', caseId.toString());
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post<EvidenceDocument[]>('/evidence/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async listCaseEvidence(caseId: number): Promise<EvidenceDocument[]> {
    const response = await apiClient.get<EvidenceDocument[]>(`/evidence/case/${caseId}`);
    return response.data;
  },

  async getEvidenceDocument(docId: number): Promise<EvidenceDocument> {
    const response = await apiClient.get<EvidenceDocument>(`/evidence/${docId}`);
    return response.data;
  },

  async reclassifyDocument(docId: number, newCategory: string): Promise<{
    document_id: number;
    previous_category: string;
    updated_category: string;
    category_title: string;
  }> {
    const response = await apiClient.patch(`/evidence/${docId}/reclassify`, {
      new_category: newCategory,
    });
    return response.data;
  },

  async deleteEvidenceDocument(docId: number): Promise<{ message: string; document_id: number }> {
    const response = await apiClient.delete(`/evidence/${docId}`);
    return response.data;
  },

  async getCaseTimeline(caseId: number): Promise<CaseTimeline> {
    const response = await apiClient.get<CaseTimeline>(`/timeline/case/${caseId}`);
    return response.data;
  },

  async addManualTimelineEvent(payload: {
    case_id: number;
    event_date: string;
    event_title: string;
    event_description: string;
    source_reference?: string;
  }): Promise<TimelineEvent> {
    const response = await apiClient.post<TimelineEvent>('/timeline/event', payload);
    return response.data;
  },

  async deleteTimelineEvent(eventId: number): Promise<{ message: string; event_id: number }> {
    const response = await apiClient.delete(`/timeline/event/${eventId}`);
    return response.data;
  },

  async checkConsistency(payload: {
    case_id: number;
    narrative: string;
    predicted_domain?: string;
    narrative_amount?: number;
    narrative_date?: string;
  }): Promise<ConsistencyCheckResponse> {
    const response = await apiClient.post<ConsistencyCheckResponse>('/evidence/consistency-check', payload);
    return response.data;
  },

  async mapEvidenceToStatute(payload: {
    narrative: string;
    act_code: string;
    section_number: string;
    case_id?: number;
    uploaded_documents?: any[];
  }): Promise<any> {
    const response = await apiClient.post('/evidence/map-to-statute', payload);
    return response.data;
  },
};
