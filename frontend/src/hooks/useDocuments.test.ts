import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDocuments } from './useDocuments';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api');

describe('useDocuments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch documents on mount', async () => {
    const mockDocuments = [
      { id: '1', title: 'Doc 1', file_name: 'doc1.pdf', file_type: 'pdf', upload_date: '2024-01-01' },
    ];

    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: mockDocuments });

    const { result } = renderHook(() => useDocuments());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.documents).toEqual(mockDocuments);
    expect(result.current.error).toBeNull();
  });

  it('should handle fetch error', async () => {
    vi.mocked(apiClient.getDocuments).mockRejectedValue(new Error('Failed to fetch'));

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch');
    expect(result.current.documents).toEqual([]);
  });

  it('should upload document', async () => {
    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const mockUploadResponse = { id: '123', filename: 'test.pdf', status: 'success' };
    const mockDocuments = [{ id: '123', title: 'test.pdf', file_name: 'test.pdf', file_type: 'pdf', upload_date: '2024-01-01' }];

    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: mockDocuments });
    vi.mocked(apiClient.uploadDocument).mockResolvedValue(mockUploadResponse);

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const uploadResult = await result.current.uploadDocument(mockFile);

    expect(uploadResult).toEqual(mockUploadResponse);
    expect(apiClient.uploadDocument).toHaveBeenCalledWith(mockFile);
    expect(apiClient.getDocuments).toHaveBeenCalledTimes(2); // Initial + after upload
  });

  it('should handle upload error', async () => {
    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: [] });
    vi.mocked(apiClient.uploadDocument).mockRejectedValue(new Error('Upload failed'));

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(result.current.uploadDocument(mockFile)).rejects.toThrow('Upload failed');
    expect(result.current.error).toBe('Upload failed');
  });

  it('should delete document', async () => {
    const mockDocuments = [
      { id: '1', title: 'Doc 1', file_name: 'doc1.pdf', file_type: 'pdf', upload_date: '2024-01-01' },
    ];

    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: mockDocuments });
    vi.mocked(apiClient.deleteDocument).mockResolvedValue({ status: 'deleted' });

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.deleteDocument('1');

    expect(apiClient.deleteDocument).toHaveBeenCalledWith('1');
    expect(apiClient.getDocuments).toHaveBeenCalledTimes(2); // Initial + after delete
  });

  it('should handle delete error', async () => {
    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: [] });
    vi.mocked(apiClient.deleteDocument).mockRejectedValue(new Error('Delete failed'));

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(result.current.deleteDocument('1')).rejects.toThrow('Delete failed');
    expect(result.current.error).toBe('Delete failed');
  });

  it('should refresh documents', async () => {
    const mockDocuments = [
      { id: '1', title: 'Doc 1', file_name: 'doc1.pdf', file_type: 'pdf', upload_date: '2024-01-01' },
    ];

    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: mockDocuments });

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.refresh();

    expect(apiClient.getDocuments).toHaveBeenCalledTimes(2); // Initial + manual refresh
  });

  it('should handle empty documents list', async () => {
    vi.mocked(apiClient.getDocuments).mockResolvedValue({ documents: [] });

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.documents).toEqual([]);
    expect(result.current.error).toBeNull();
  });
});