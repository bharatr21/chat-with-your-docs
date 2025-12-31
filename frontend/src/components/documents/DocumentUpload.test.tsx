import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DocumentUpload } from './DocumentUpload';

describe('DocumentUpload', () => {
  it('should render upload area', () => {
    const onUpload = vi.fn();
    render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    expect(screen.getByText(/Drop a file or click to upload/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, DOCX, TXT, CSV/i)).toBeInTheDocument();
  });

  it('should show uploading state', () => {
    const onUpload = vi.fn();
    render(<DocumentUpload onUpload={onUpload} isUploading={true} />);
    
    expect(screen.getByText(/Uploading.../i)).toBeInTheDocument();
  });

  it('should validate file type', async () => {
    const onUpload = vi.fn();
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const invalidFile = new File(['content'], 'test.exe', { type: 'application/exe' });
    
    Object.defineProperty(input, 'files', {
      value: [invalidFile],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
    });
    
    expect(onUpload).not.toHaveBeenCalled();
  });

  it('should validate file size', async () => {
    const onUpload = vi.fn();
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(input, 'files', {
      value: [largeFile],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText(/File too large/i)).toBeInTheDocument();
    });
    
    expect(onUpload).not.toHaveBeenCalled();
  });

  it('should call onUpload with valid file', async () => {
    const onUpload = vi.fn().mockResolvedValue(undefined);
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(input, 'files', {
      value: [validFile],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith(validFile);
    });
  });

  it('should accept PDF files', async () => {
    const onUpload = vi.fn().mockResolvedValue(undefined);
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const pdfFile = new File(['pdf content'], 'document.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(input, 'files', {
      value: [pdfFile],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(onUpload).toHaveBeenCalled();
    });
  });

  it('should accept DOCX files', async () => {
    const onUpload = vi.fn().mockResolvedValue(undefined);
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const docxFile = new File(['docx content'], 'document.docx', { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    });
    
    Object.defineProperty(input, 'files', {
      value: [docxFile],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(onUpload).toHaveBeenCalled();
    });
  });

  it('should handle upload error', async () => {
    const onUpload = vi.fn().mockRejectedValue(new Error('Upload failed'));
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(input, 'files', {
      value: [validFile],
      writable: false,
    });
    
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
    });
  });

  it('should clear error on new file selection', async () => {
    const onUpload = vi.fn()
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce(undefined);
    
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file1 = new File(['content'], 'test1.pdf', { type: 'application/pdf' });
    
    // First upload - fails
    Object.defineProperty(input, 'files', {
      value: [file1],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(/First error/i)).toBeInTheDocument();
    });

    // Second upload - succeeds
    const file2 = new File(['content'], 'test2.pdf', { type: 'application/pdf' });
    Object.defineProperty(input, 'files', {
      value: [file2],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);
    
    await waitFor(() => {
      expect(screen.queryByText(/First error/i)).not.toBeInTheDocument();
    });
  });

  it('should reset input after file selection', async () => {
    const onUpload = vi.fn().mockResolvedValue(undefined);
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });

    fireEvent.change(input);

    // Input value should be reset to allow same file selection again
    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('should disable interactions when uploading', () => {
    const onUpload = vi.fn();
    const { container } = render(<DocumentUpload onUpload={onUpload} isUploading={true} />);
    
    const dropZone = container.querySelector('.pointer-events-none');
    expect(dropZone).toBeInTheDocument();
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });
});