'use client';

import { useState, useRef, useCallback } from 'react';
import { Upload, X, Loader2 } from 'lucide-react';

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

const ACCEPTED_TYPES = ['.pdf', '.docx', '.txt', '.md', '.csv'];
const MAX_SIZE = 100 * 1024 * 1024; // 50MB

export function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(extension)) {
      return `Invalid file type. Accepted: ${ACCEPTED_TYPES.join(', ')}`;
    }
    if (file.size > MAX_SIZE) {
      return 'File too large. Maximum size is 50MB.';
    }
    return null;
  }, []);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      await onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  }, [onUpload, validateFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleClick = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  return (
    <div className="space-y-2">
      <div
        role="button"
        tabIndex={0}
        aria-disabled={isUploading}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative border-2 border-dashed rounded-lg p-6 cursor-pointer
          transition-colors duration-200
          ${isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
          ${isUploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES.join(',')}
          onChange={handleInputChange}
          className="hidden"
          disabled={isUploading}
        />

        <div className="flex flex-col items-center gap-2 text-center">
          {isUploading ? (
            <>
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-muted-foreground">Uploading...</p>
            </>
          ) : (
            <>
              <Upload className="w-8 h-8 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Drop a file or click to upload</p>
                <p className="text-xs text-muted-foreground mt-1">
                  PDF, DOCX, TXT, CSV (max 50MB)
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <X className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
