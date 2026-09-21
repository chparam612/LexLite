import axios from 'axios';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }
    return Promise.reject(error);
  }
);

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    firebase_uid?: string | null;
    email: string;
    display_name?: string | null;
    created_at: string;
    updated_at: string;
  };
}

export const authApi = {
  register: async (email: string, password: string, displayName?: string): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/api/v1/auth/register', {
      email,
      password,
      display_name: displayName,
    });
    return res.data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/api/v1/auth/login', {
      email,
      password,
    });
    return res.data;
  },

  demoLogin: async (): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/api/v1/auth/demo-login');
    return res.data;
  },

  getMe: async () => {
    const res = await apiClient.get('/api/v1/auth/me');
    return res.data;
  },
};

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: string;
  components: {
    database: string;
    storage: string;
  };
  timestamp: string;
}

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export const checkReadiness = async (): Promise<ReadinessResponse> => {
  const response = await apiClient.get<ReadinessResponse>('/ready');
  return response.data;
};

export interface Citation {
  id: string;
  chunk_id: string;
  page_number: number;
  section_label?: string;
  quoted_text: string;
  citation_order: number;
  document_title?: string;
}

export interface Claim {
  id: string;
  claim_text: string;
  claim_type: string;
  support_status: string;
}

export interface ProcessingDetails {
  candidate_chunks_retrieved: number;
  context_chunks_used: number;
  verification_status: string;
  retrieval_method: string;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  model_name?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  model_name?: string;
  citations: Citation[];
  claims: Claim[];
  processing_details?: ProcessingDetails;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  document_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export const createConversation = async (
  title?: string,
  document_ids?: string[]
): Promise<Conversation> => {
  const response = await apiClient.post<Conversation>('/api/v1/conversations', {
    title: title || 'New Legal Research',
    document_ids: document_ids || [],
  });
  return response.data;
};

export const listConversations = async (): Promise<Conversation[]> => {
  const response = await apiClient.get<Conversation[]>('/api/v1/conversations');
  return response.data;
};

export const getConversation = async (id: string): Promise<ConversationDetail> => {
  const response = await apiClient.get<ConversationDetail>(`/api/v1/conversations/${id}`);
  return response.data;
};

export const deleteConversation = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/conversations/${id}`);
};

export const sendMessage = async (
  conversationId: string,
  content: string
): Promise<Message> => {
  const response = await apiClient.post<Message>(
    `/api/v1/conversations/${conversationId}/messages`,
    { content }
  );
  return response.data;
};

// ---------------------------------------------------------------------
// Demo & Synthetic Document API
// ---------------------------------------------------------------------

export interface LoadSampleDocumentResponse {
  status: string;
  message: string;
  document: {
    id: string;
    title: string;
    filename: string;
    file_size_bytes: number;
    status: string;
    page_count: number;
  };
}

export const loadSampleDocument = async (): Promise<LoadSampleDocumentResponse> => {
  const response = await apiClient.post<LoadSampleDocumentResponse>('/api/v1/demo/load-sample');
  return response.data;
};

export const getSampleDocumentPdfUrl = (): string => {
  return `${API_BASE_URL}/api/v1/demo/sample-document`;
};

// ---------------------------------------------------------------------
// Evaluation Suite API
// ---------------------------------------------------------------------

export interface TestCaseResult {
  test_id: string;
  category: string;
  name: string;
  input_description: string;
  expected_behavior: string;
  actual_result: string;
  status: string;
  duration_ms: number;
}

export interface EvaluationSummary {
  total_tests: number;
  passed: number;
  failed: number;
  blocked: number;
  execution_time_ms: number;
  results: TestCaseResult[];
}

export const runEvaluation = async (): Promise<EvaluationSummary> => {
  const response = await apiClient.post<EvaluationSummary>('/api/v1/evaluation/run');
  return response.data;
};


