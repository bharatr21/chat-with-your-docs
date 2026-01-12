import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MessageInput } from './MessageInput';

describe('MessageInput', () => {
  const defaultProps = {
    input: '',
    handleInputChange: vi.fn(),
    handleSubmit: vi.fn(),
    isLoading: false,
    disabled: false,
  };

  it('renders input field', () => {
    render(<MessageInput {...defaultProps} />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<MessageInput {...defaultProps} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows placeholder when disabled', () => {
    render(<MessageInput {...defaultProps} disabled={true} />);
    expect(screen.getByPlaceholderText(/select documents/i)).toBeInTheDocument();
  });

  it('shows default placeholder when enabled', () => {
    render(<MessageInput {...defaultProps} />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
  });

  it('disables input when loading', () => {
    render(<MessageInput {...defaultProps} isLoading={true} />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('disables button when input is empty', () => {
    render(<MessageInput {...defaultProps} input="" />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('enables button when input has text', () => {
    render(<MessageInput {...defaultProps} input="Hello" />);
    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('calls handleInputChange on input', () => {
    const handleInputChange = vi.fn();
    render(<MessageInput {...defaultProps} handleInputChange={handleInputChange} />);

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } });
    expect(handleInputChange).toHaveBeenCalled();
  });

  it('calls handleSubmit on form submit', () => {
    const handleSubmit = vi.fn((e) => e.preventDefault());
    render(<MessageInput {...defaultProps} input="test" handleSubmit={handleSubmit} />);

    fireEvent.submit(screen.getByRole('button').closest('form')!);
    expect(handleSubmit).toHaveBeenCalled();
  });
});
