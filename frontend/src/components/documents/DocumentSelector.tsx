'use client';

import { FileText, Trash2, Check } from 'lucide-react';
import type { Document } from '@/types/document';
import { formatFileSize } from '@/lib/utils';

interface DocumentSelectorProps {
  documents: Document[];
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  onDelete: (id: string) => void;
  isLoading: boolean;
}

export function DocumentSelector({
  documents,
  selectedIds,
  onSelectionChange,
  onDelete,
  isLoading,
}: DocumentSelectorProps) {
  const toggleDocument = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((docId) => docId !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  const selectAll = () => {
    if (selectedIds.length === documents.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(documents.map((doc) => doc.id));
    }
  };

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-2">
        <span className="text-sm text-muted-foreground">
          {selectedIds.length} of {documents.length} selected
        </span>
        <button
          onClick={selectAll}
          className="text-xs text-primary hover:underline"
          disabled={isLoading}
        >
          {selectedIds.length === documents.length ? 'Deselect all' : 'Select all'}
        </button>
      </div>

      <div className="space-y-1 max-h-64 overflow-y-auto">
        {documents.map((doc) => {
          const isSelected = selectedIds.includes(doc.id);

          return (
            <div
              key={doc.id}
              className={`
                flex items-center gap-2 p-2 rounded-lg cursor-pointer
                transition-colors duration-150
                ${isSelected ? 'bg-primary/10 border border-primary/30' : 'hover:bg-muted'}
              `}
              onClick={() => toggleDocument(doc.id)}
            >
              <div
                className={`
                  w-5 h-5 rounded border flex items-center justify-center flex-shrink-0
                  ${isSelected ? 'bg-primary border-primary' : 'border-muted-foreground/30'}
                `}
              >
                {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
              </div>

              <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{doc.title || doc.file_name}</p>
                <p className="text-xs text-muted-foreground">
                  {doc.file_type.toUpperCase()} · {formatFileSize(doc.file_size || 0)}
                  {doc.chunk_count && ` · ${doc.chunk_count} chunks`}
                </p>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(doc.id);
                }}
                aria-label={`Delete ${doc.title || doc.file_name}`}
                className="p-1 text-muted-foreground hover:text-destructive rounded transition-colors"
                disabled={isLoading}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
