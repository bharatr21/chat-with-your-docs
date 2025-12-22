export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatSession {
  id: string;
  name?: string;
  model_id: string;
  document_ids: string[];
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}
