'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import type { Model, ModelGroup } from '@/types/model';

export function useModels() {
  const [models, setModels] = useState<Model[]>([]);
  const [groupedModels, setGroupedModels] = useState<ModelGroup[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiClient.getModels();
        const modelList = response.models || [];

        // Filter only available models
        const availableModels = modelList.filter((m: Model) => m.available);
        setModels(availableModels);

        // Group models by provider
        const groups = availableModels.reduce((acc: Record<string, Model[]>, model: Model) => {
          if (!acc[model.provider]) {
            acc[model.provider] = [];
          }
          acc[model.provider].push(model);
          return acc;
        }, {});

        const grouped = Object.entries(groups).map(([provider, models]) => ({
          provider,
          models: models as Model[],
        }));

        setGroupedModels(grouped);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch models');
      } finally {
        setIsLoading(false);
      }
    };

    fetchModels();
  }, []);

  return { models, groupedModels, isLoading, error };
}
