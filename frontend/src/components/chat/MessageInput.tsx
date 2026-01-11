'use client';

import { FormEvent, ChangeEvent } from 'react';
import { Send } from 'lucide-react';

interface MessageInputProps {
  input: string;
  handleInputChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function MessageInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  disabled,
}: MessageInputProps) {
  return (
    <form onSubmit={handleSubmit} className="p-4 border-t bg-background">
      <div className="max-w-4xl mx-auto flex gap-2">
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder={
            disabled
              ? 'Please select documents to start chatting...'
              : 'Ask a question about your documents...'
          }
          disabled={isLoading || disabled}
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || disabled || !input.trim()}
          aria-label="Send message"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </form>
  );
}
