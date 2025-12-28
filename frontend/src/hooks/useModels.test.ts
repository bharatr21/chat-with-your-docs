import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useModels } from './useModels';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api');

describe('useModels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch models on mount', async () => {
    const mockModels = [
      { id: 'model-1', name: 'Model 1', provider: 'OpenAI', available: true },
      { id: 'model-2', name: 'Model 2', provider: 'Anthropic', available: true },
    ];

    vi.mocked(apiClient.getModels).mockResolvedValue({ models: mockModels });

    const { result } = renderHook(() => useModels());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.models).toEqual(mockModels);
    expect(result.current.error).toBeNull();
  });

  it('should filter only available models', async () => {
    const mockModels = [
      { id: 'model-1', name: 'Model 1', provider: 'OpenAI', available: true },
      { id: 'model-2', name: 'Model 2', provider: 'Anthropic', available: false },
      { id: 'model-3', name: 'Model 3', provider: 'Google', available: true },
    ];

    vi.mocked(apiClient.getModels).mockResolvedValue({ models: mockModels });

    const { result } = renderHook(() => useModels());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.models).toHaveLength(2);
    expect(result.current.models.every(m => m.available)).toBe(true);
  });

  it('should group models by provider', async () => {
    const mockModels = [
      { id: 'openai-1', name: 'GPT 4', provider: 'OpenAI', available: true },
      { id: 'openai-2', name: 'GPT 3.5', provider: 'OpenAI', available: true },
      { id: 'anthropic-1', name: 'Claude', provider: 'Anthropic', available: true },
    ];

    vi.mocked(apiClient.getModels).mockResolvedValue({ models: mockModels });

    const { result } = renderHook(() => useModels());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.groupedModels).toHaveLength(2);
    
    const openaiGroup = result.current.groupedModels.find(g => g.provider === 'OpenAI');
    expect(openaiGroup?.models).toHaveLength(2);
    
    const anthropicGroup = result.current.groupedModels.find(g => g.provider === 'Anthropic');
    expect(anthropicGroup?.models).toHaveLength(1);
  });

  it('should handle fetch error', async () => {
    vi.mocked(apiClient.getModels).mockRejectedValue(new Error('Failed to fetch models'));

    const { result } = renderHook(() => useModels());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch models');
    expect(result.current.models).toEqual([]);
  });

  it('should handle empty models list', async () => {
    vi.mocked(apiClient.getModels).mockResolvedValue({ models: [] });

    const { result } = renderHook(() => useModels());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.models).toEqual([]);
    expect(result.current.groupedModels).toEqual([]);
  });

  it('should handle null or undefined models response', async () => {
    vi.mocked(apiClient.getModels).mockResolvedValue({ models: undefined as any });

    const { result } = renderHook(() => useModels());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.models).toEqual([]);
  });

  it('should group single provider correctly', async () => {
    const mockModels = [
      { id: 'model-1', name: 'Model 1', provider: 'OpenAI', available: true },
      { id: 'model-2', name: 'Model 2', provider: 'OpenAI', available: true },
    ];

    vi.mocked(apiClient.getModels).mockResolvedValue({ models: mockModels });

    const { result } = renderHook(() => useModels());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.groupedModels).toHaveLength(1);
    expect(result.current.groupedModels[0].provider).toBe('OpenAI');
    expect(result.current.groupedModels[0].models).toHaveLength(2);
  });
});