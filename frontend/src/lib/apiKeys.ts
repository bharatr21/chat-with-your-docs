/**
 * API Keys management utilities
 * Stores user-provided API keys in localStorage
 */

export interface APIKeys {
  openai?: string;
  anthropic?: string;
  gemini?: string;
  huggingface?: string;
}

const STORAGE_KEY = 'chat-app-api-keys';

/**
 * Get API keys from localStorage
 */
export function getAPIKeys(): APIKeys {
  if (typeof window === 'undefined') return {};

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return {};
    return JSON.parse(stored);
  } catch (error) {
    console.error('Failed to load API keys:', error);
    return {};
  }
}

/**
 * Save API keys to localStorage
 */
export function saveAPIKeys(keys: APIKeys): void {
  if (typeof window === 'undefined') return;

  try {
    // Filter out empty strings
    const filtered: APIKeys = {};
    if (keys.openai?.trim()) filtered.openai = keys.openai.trim();
    if (keys.anthropic?.trim()) filtered.anthropic = keys.anthropic.trim();
    if (keys.gemini?.trim()) filtered.gemini = keys.gemini.trim();
    if (keys.huggingface?.trim()) filtered.huggingface = keys.huggingface.trim();

    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Failed to save API keys:', error);
  }
}

/**
 * Clear all API keys from localStorage
 */
export function clearAPIKeys(): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear API keys:', error);
  }
}

/**
 * Get headers with API keys for API requests
 */
export function getAPIKeyHeaders(): Record<string, string> {
  const keys = getAPIKeys();
  const headers: Record<string, string> = {};

  if (keys.openai) headers['X-OpenAI-API-Key'] = keys.openai;
  if (keys.anthropic) headers['X-Anthropic-API-Key'] = keys.anthropic;
  if (keys.gemini) headers['X-Gemini-API-Key'] = keys.gemini;
  if (keys.huggingface) headers['X-HF-API-Key'] = keys.huggingface;

  return headers;
}
