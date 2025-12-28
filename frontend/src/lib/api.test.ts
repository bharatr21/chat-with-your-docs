import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from './api';

// Mock fetch globally
global.fetch = vi.fn();

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDocuments', () => {
    it('should fetch documents successfully', async () => {
      const mockDocuments = [
        { id: '1', title: 'Doc 1', file_name: 'doc1.pdf', file_type: 'pdf' },
        { id: '2', title: 'Doc 2', file_name: 'doc2.pdf', file_type: 'pdf' },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ documents: mockDocuments }),
      });

      const result = await apiClient.getDocuments();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/documents',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result.documents).toEqual(mockDocuments);
    });

    it('should handle fetch error', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Internal Server Error',
      });

      await expect(apiClient.getDocuments()).rejects.toThrow();
    });
  });

  describe('uploadDocument', () => {
    it('should upload file successfully', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse = {
        id: '123',
        filename: 'test.pdf',
        status: 'success',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiClient.uploadDocument(mockFile);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/documents/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle upload error', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'File too large',
      });

      await expect(apiClient.uploadDocument(mockFile)).rejects.toThrow('File too large');
    });
  });

  describe('deleteDocument', () => {
    it('should delete document successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'deleted' }),
      });

      await apiClient.deleteDocument('doc-123');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/documents/doc-123',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('getModels', () => {
    it('should fetch models successfully', async () => {
      const mockModels = [
        { id: 'model-1', name: 'Model 1', provider: 'OpenAI', available: true },
        { id: 'model-2', name: 'Model 2', provider: 'Anthropic', available: true },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ models: mockModels }),
      });

      const result = await apiClient.getModels();

      expect(result.models).toEqual(mockModels);
    });
  });

  describe('sessions', () => {
    it('should create session', async () => {
      const mockSession = { session_id: 'session-123' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      });

      const result = await apiClient.createSession('model-1');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/sessions',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ model_id: 'model-1' }),
        })
      );
      expect(result).toEqual(mockSession);
    });

    it('should get sessions', async () => {
      const mockSessions = [
        { id: '1', created_at: '2024-01-01', selected_model_id: 'model-1' },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: mockSessions }),
      });

      const result = await apiClient.getSessions();

      expect(result.sessions).toEqual(mockSessions);
    });

    it('should get specific session', async () => {
      const mockSession = {
        id: 'session-123',
        messages: [],
        selected_model_id: 'model-1',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      });

      const result = await apiClient.getSession('session-123');

      expect(result).toEqual(mockSession);
    });

    it('should delete session', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'deleted' }),
      });

      await apiClient.deleteSession('session-123');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/sessions/session-123',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('error handling', () => {
    it('should throw error with response text', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => 'Resource not found',
      });

      await expect(apiClient.getDocuments()).rejects.toThrow('Resource not found');
    });

    it('should throw error with HTTP status when no text', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => '',
      });

      await expect(apiClient.getDocuments()).rejects.toThrow('HTTP 500');
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.getDocuments()).rejects.toThrow('Network error');
    });
  });

  describe('API URL configuration', () => {
    it('should use environment variable for base URL', () => {
      // The API URL is set in setup.ts via vi.stubEnv
      expect(process.env.NEXT_PUBLIC_API_URL).toBe('http://localhost:8000');
    });
  });
});