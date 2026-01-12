import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentSelector } from './DocumentSelector';

describe('DocumentSelector', () => {
  const mockDocuments = [
    {
      id: 'doc-1',
      title: 'Test Document',
      file_name: 'test.pdf',
      file_type: 'pdf',
      file_size: 1024,
      chunk_count: 5,
    },
    {
      id: 'doc-2',
      title: 'Another Doc',
      file_name: 'another.txt',
      file_type: 'txt',
      file_size: 512,
      chunk_count: 2,
    },
  ];

  const defaultProps = {
    documents: mockDocuments,
    selectedIds: [],
    onSelectionChange: vi.fn(),
    onDelete: vi.fn(),
    isLoading: false,
  };

  it('renders document list', () => {
    render(<DocumentSelector {...defaultProps} />);
    expect(screen.getByText('Test Document')).toBeInTheDocument();
    expect(screen.getByText('Another Doc')).toBeInTheDocument();
  });

  it('shows empty state when no documents', () => {
    render(<DocumentSelector {...defaultProps} documents={[]} />);
    expect(screen.getByText(/no documents uploaded/i)).toBeInTheDocument();
  });

  it('shows selection count', () => {
    render(<DocumentSelector {...defaultProps} selectedIds={['doc-1']} />);
    expect(screen.getByText('1 of 2 selected')).toBeInTheDocument();
  });

  it('toggles document selection', () => {
    const onSelectionChange = vi.fn();
    render(<DocumentSelector {...defaultProps} onSelectionChange={onSelectionChange} />);

    fireEvent.click(screen.getByText('Test Document'));
    expect(onSelectionChange).toHaveBeenCalledWith(['doc-1']);
  });

  it('deselects document when already selected', () => {
    const onSelectionChange = vi.fn();
    render(
      <DocumentSelector
        {...defaultProps}
        selectedIds={['doc-1']}
        onSelectionChange={onSelectionChange}
      />
    );

    fireEvent.click(screen.getByText('Test Document'));
    expect(onSelectionChange).toHaveBeenCalledWith([]);
  });

  it('selects all documents', () => {
    const onSelectionChange = vi.fn();
    render(<DocumentSelector {...defaultProps} onSelectionChange={onSelectionChange} />);

    fireEvent.click(screen.getByText('Select all'));
    expect(onSelectionChange).toHaveBeenCalledWith(['doc-1', 'doc-2']);
  });

  it('deselects all when all selected', () => {
    const onSelectionChange = vi.fn();
    render(
      <DocumentSelector
        {...defaultProps}
        selectedIds={['doc-1', 'doc-2']}
        onSelectionChange={onSelectionChange}
      />
    );

    fireEvent.click(screen.getByText('Deselect all'));
    expect(onSelectionChange).toHaveBeenCalledWith([]);
  });

  it('shows file info', () => {
    render(<DocumentSelector {...defaultProps} />);
    expect(screen.getByText(/PDF/)).toBeInTheDocument();
    expect(screen.getByText(/5 chunks/)).toBeInTheDocument();
  });
});
