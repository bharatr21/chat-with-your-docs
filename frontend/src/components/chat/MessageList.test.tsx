import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageList } from './MessageList';

describe('MessageList', () => {
  it('should show empty state when no messages', () => {
    render(<MessageList messages={[]} isLoading={false} />);
    
    expect(screen.getByText(/Start a conversation/i)).toBeInTheDocument();
    expect(screen.getByText(/Make sure to select documents first/i)).toBeInTheDocument();
  });

  it('should render user messages', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Hello, how are you?' },
    ];
    
    render(<MessageList messages={messages} isLoading={false} />);
    
    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
  });

  it('should render assistant messages', () => {
    const messages = [
      { id: '1', role: 'assistant' as const, content: 'I am doing well, thank you!' },
    ];
    
    render(<MessageList messages={messages} isLoading={false} />);
    
    expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument();
  });

  it('should render conversation with multiple messages', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Hello' },
      { id: '2', role: 'assistant' as const, content: 'Hi there!' },
      { id: '3', role: 'user' as const, content: 'How can you help?' },
    ];
    
    render(<MessageList messages={messages} isLoading={false} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
    expect(screen.getByText('How can you help?')).toBeInTheDocument();
  });

  it('should show loading indicator when loading', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Test question' },
    ];
    
    render(<MessageList messages={messages} isLoading={true} />);
    
    // Should show animated dots
    const dots = document.querySelectorAll('.animate-bounce');
    expect(dots.length).toBeGreaterThan(0);
  });

  it('should not show loading indicator when not loading', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Test' },
    ];
    
    render(<MessageList messages={messages} isLoading={false} />);
    
    const dots = document.querySelectorAll('.animate-bounce');
    expect(dots.length).toBe(0);
  });

  it('should handle messages with special characters', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Test with\nnewlines\nand special chars: @#$%' },
    ];
    
    render(<MessageList messages={messages} isLoading={false} />);
    
    expect(screen.getByText(/Test with/)).toBeInTheDocument();
  });

  it('should render icons for user and assistant', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'User message' },
      { id: '2', role: 'assistant' as const, content: 'Assistant message' },
    ];
    
    render(<MessageList messages={messages} isLoading={false} />);
    
    // Check for user and bot icons (lucide-react icons)
    const icons = document.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });
});