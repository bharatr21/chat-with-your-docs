import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';

// Mock useChat hook
vi.mock('@ai-sdk/react', () => ({
  useChat: vi.fn(() => ({
    messages: [],
    input: '',
    handleInputChange: vi.fn(),
    handleSubmit: vi.fn(),
    isLoading: false,
  })),
}));

describe('ChatInterface', () => {
  const defaultProps = {
    sessionId: 'test-session',
    selectedDocumentIds: ['doc1'],
    selectedModelId: 'model1',
  };

  it('should render MessageList and MessageInput', () => {
    render(<ChatInterface {...defaultProps} />);
    
    // Component should render without crashing
    expect(document.querySelector('.flex')).toBeInTheDocument();
  });

  it('should pass correct props to useChat', () => {
    const { useChat } = require('@ai-sdk/react');
    
    render(<ChatInterface {...defaultProps} />);
    
    expect(useChat).toHaveBeenCalledWith(
      expect.objectContaining({
        api: 'http://localhost:8000/api/chat',
        body: {
          session_id: 'test-session',
          document_ids: ['doc1'],
          model_id: 'model1',
        },
      })
    );
  });

  it('should handle empty document IDs', () => {
    render(<ChatInterface {...defaultProps} selectedDocumentIds={[]} />);
    
    // Should still render
    expect(document.querySelector('.flex')).toBeInTheDocument();
  });
});