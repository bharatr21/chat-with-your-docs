import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelSelector } from './ModelSelector';

describe('ModelSelector', () => {
  const mockGroups = [
    {
      provider: 'HuggingFace',
      models: [
        { id: 'hf-1', name: 'Mixtral 8x7B', provider: 'HuggingFace', available: true },
      ],
    },
    {
      provider: 'OpenAI',
      models: [
        { id: 'openai-1', name: 'GPT-5 Mini', provider: 'OpenAI', available: true },
      ],
    },
  ];

  const defaultProps = {
    groupedModels: mockGroups,
    selectedModelId: 'hf-1',
    onModelChange: vi.fn(),
    isLoading: false,
  };

  it('renders selected model name', () => {
    render(<ModelSelector {...defaultProps} />);
    expect(screen.getByText('Mixtral 8x7B')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ModelSelector {...defaultProps} isLoading={true} />);
    expect(screen.getByText(/loading models/i)).toBeInTheDocument();
  });

  it('shows no models message when empty', () => {
    render(<ModelSelector {...defaultProps} groupedModels={[]} />);
    expect(screen.getByText(/no models available/i)).toBeInTheDocument();
  });

  it('opens dropdown on click', () => {
    render(<ModelSelector {...defaultProps} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('HUGGINGFACE')).toBeInTheDocument();
    expect(screen.getByText('OPENAI')).toBeInTheDocument();
  });

  it('calls onModelChange when model selected', () => {
    const onModelChange = vi.fn();
    render(<ModelSelector {...defaultProps} onModelChange={onModelChange} />);

    fireEvent.click(screen.getByRole('button'));
    fireEvent.click(screen.getByText('GPT-5 Mini'));

    expect(onModelChange).toHaveBeenCalledWith('openai-1');
  });

  it('shows check mark for selected model', () => {
    render(<ModelSelector {...defaultProps} />);
    fireEvent.click(screen.getByRole('button'));

    // The selected model should have a check icon (we can check by class or role)
    const mixtralOption = screen.getByText('Mixtral 8x7B').closest('button');
    expect(mixtralOption?.querySelector('svg')).toBeInTheDocument();
  });
});
