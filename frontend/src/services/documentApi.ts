import { apiClient, API_BASE_URL } from './api';

export interface DocumentItem {
  id: string;
  owner_id: string;
  title: string;
  document_type: string | null;
  jurisdiction: string | null;
  language: string;
  status: string;
  page_count: number;
  file_size: number;
  checksum: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentItem {
  versions: Array<{
    id: string;
    version_number: number;
    extraction_status: string;
    processing_error: string | null;
    created_at: string;
  }>;
}

export interface DocumentStatus {
  document_id: string;
  status: string;
  current_step: string;
  progress_percentage: number;
  error: string | null;
  updated_at: string;
}

export const fetchDocuments = async (): Promise<DocumentItem[]> => {
  const res = await apiClient.get<DocumentItem[]>('/api/v1/documents');
  return res.data;
};

export const fetchDocument = async (documentId: string): Promise<DocumentDetail> => {
  const res = await apiClient.get<DocumentDetail>(`/api/v1/documents/${documentId}`);
  return res.data;
};

export const uploadDocument = async (formData: FormData): Promise<{ document: DocumentItem; message: string }> => {
  const res = await apiClient.post<{ document: DocumentItem; message: string }>(
    '/api/v1/documents/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return res.data;
};

export const deleteDocument = async (documentId: string): Promise<void> => {
  await apiClient.delete(`/api/v1/documents/${documentId}`);
};

export const fetchDocumentStatus = async (documentId: string): Promise<DocumentStatus> => {
  const res = await apiClient.get<DocumentStatus>(`/api/v1/documents/${documentId}/status`);
  return res.data;
};

export const retryDocumentProcessing = async (documentId: string): Promise<DocumentItem> => {
  const res = await apiClient.post<DocumentItem>(`/api/v1/documents/${documentId}/retry`);
  return res.data;
};

export const getDocumentDownloadUrl = (documentId: string): string => {
  return `${API_BASE_URL}/api/v1/documents/${documentId}/download`;
};

