/**
 * LegalEase AI - Legal Drafting Studio Service (Phase 6)
 * Client for generating, previewing, editing, and exporting court-ready legal drafts.
 */

import { apiClient } from './api';

export interface PartyDetails {
  name: string;
  address?: string;
  phone?: string;
  email?: string;
  designation?: string;
  role?: string;
}

export interface MissingInfoItem {
  field: string;
  rationale: string;
  impact: string;
  suggested_prompt: string;
}

export interface VerifiedCitationItem {
  act_code: string;
  act_title: string;
  section_number: string;
  section_title: string;
  source_url: string;
  is_verified: boolean;
}

export interface ExhibitItem {
  exhibit_label: string;
  filename: string;
  category: string;
  relevance: string;
}

export interface DraftGenerateRequest {
  case_id?: number;
  draft_type: string;
  title?: string;
  narrative?: string;
  complainant?: PartyDetails;
  opposite_party?: PartyDetails;
  incident_date?: string;
  incident_location?: string;
  jurisdiction_forum?: string;
  monetary_claim?: number;
  custom_prayers?: string[];
  selected_evidence_ids?: number[];
  additional_facts?: string;
}

export interface DraftUpdateRequest {
  title?: string;
  content_markdown: string;
}

export interface DraftResponse {
  id: number;
  case_id: number;
  draft_type: string;
  title: string;
  content_markdown: string;
  pdf_path?: string;
  docx_path?: string;
  missing_information: MissingInfoItem[];
  verified_citations: VerifiedCitationItem[];
  exhibits: ExhibitItem[];
  disclaimer: string;
  created_at?: string;
  updated_at?: string;
}

export const DraftService = {
  /**
   * Generates a new legal draft grounded in case facts and canonical Bare Acts.
   */
  async generateDraft(data: DraftGenerateRequest): Promise<DraftResponse> {
    const response = await apiClient.post<DraftResponse>('/drafts/generate', data);
    return response.data;
  },

  /**
   * Retrieves a draft by ID.
   */
  async getDraft(id: number): Promise<DraftResponse> {
    const response = await apiClient.get<DraftResponse>(`/drafts/${id}`);
    return response.data;
  },

  /**
   * Lists all drafts associated with a specific case.
   */
  async listCaseDrafts(caseId: number): Promise<DraftResponse[]> {
    const response = await apiClient.get<DraftResponse[]>(`/drafts/case/${caseId}`);
    return response.data;
  },

  /**
   * Updates draft content markdown or title.
   */
  async updateDraft(id: number, data: DraftUpdateRequest): Promise<DraftResponse> {
    const response = await apiClient.put<DraftResponse>(`/drafts/${id}`, data);
    return response.data;
  },

  /**
   * Gets the direct URL for downloading PDF.
   */
  getPdfDownloadUrl(id: number): string {
    return `/api/v1/drafts/${id}/export/pdf`;
  },

  /**
   * Gets the direct URL for downloading DOCX.
   */
  getDocxDownloadUrl(id: number): string {
    return `/api/v1/drafts/${id}/export/docx`;
  },

  /**
   * Deletes a draft and its exported files.
   */
  async deleteDraft(id: number): Promise<void> {
    await apiClient.delete(`/drafts/${id}`);
  },
};
