import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  model_name?: string;
  citations: Citation[];
  claims: Claim[];
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

