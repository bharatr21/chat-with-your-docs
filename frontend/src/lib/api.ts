import { getAPIKeyHeaders } from './apiKeys';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...getAPIKeyHeaders(), // Include user API keys from localStorage
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Documents
  async getDocuments() {
    return this.request<{ documents: Document[] }>('/api/documents');
  }

  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      headers: getAPIKeyHeaders(), // Include user API keys
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async deleteDocument(documentId: string) {
    return this.request(`/api/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  // Models
  async getModels() {
    return this.request<{ models: Model[] }>('/api/models');
  }

  // Sessions
  async createSession(modelId: string) {
    return this.request<{ session_id: string }>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId }),
    });
  }

  async getSessions() {
    return this.request<{ sessions: Session[] }>('/api/sessions');
  }

  async getSession(sessionId: string) {
    return this.request<Session>(`/api/sessions/${sessionId}`);
  }

  async deleteSession(sessionId: string) {
    return this.request(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }
}

// Types
interface Document {
  id: string;
  title: string;
  file_name: string;
  file_type: string;
  file_size?: number;
  chunk_count?: number;
  upload_date: string;
}

interface Model {
  id: string;
  name: string;
  provider: string;
  description?: string;
  available: boolean;
}

interface Session {
  id: string;
  created_at: string;
  updated_at: string;
  selected_doc_ids: string[];
  selected_model_id: string;
  messages: Message[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const apiClient = new ApiClient(API_URL);
