'use client';

import { useState } from 'react';
import { ChevronDown, Cpu, Check, Loader2 } from 'lucide-react';
import type { Model, ModelGroup } from '@/types/model';

interface ModelSelectorProps {
  groupedModels: ModelGroup[];
  selectedModelId: string;
  onModelChange: (modelId: string) => void;
  isLoading: boolean;
}

export function ModelSelector({
  groupedModels,
  selectedModelId,
  onModelChange,
  isLoading,
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedModel = groupedModels
    .flatMap((group) => group.models)
    .find((model) => model.id === selectedModelId);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 border rounded-lg bg-muted/50">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Loading models...</span>
      </div>
    );
  }

  if (groupedModels.length === 0) {
    return (
      <div className="px-3 py-2 border rounded-lg bg-muted/50">
        <span className="text-sm text-muted-foreground">No models available</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 border rounded-lg hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">
            {selectedModel?.name || 'Select a model'}
          </span>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-muted-foreground transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 mt-1 w-full border rounded-lg bg-background shadow-lg max-h-72 overflow-y-auto">
            {groupedModels.map((group) => (
              <div key={group.provider}>
                <div className="px-3 py-2 bg-muted/50 border-b">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">
                    {group.provider}
                  </span>
                </div>
                {group.models.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => {
                      onModelChange(model.id);
                      setIsOpen(false);
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/50 transition-colors"
                  >
                    <div className="text-left">
                      <p className="text-sm font-medium">{model.name}</p>
                      {model.description && (
                        <p className="text-xs text-muted-foreground">
                          {model.description}
                        </p>
                      )}
                    </div>
                    {model.id === selectedModelId && (
                      <Check className="w-4 h-4 text-primary flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
