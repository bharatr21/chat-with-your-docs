export interface Document {
  id: string;
  title: string;
  file_name: string;
  file_type: string;
  file_size?: number;
  page_count?: number;
  headers?: string[];
  chunk_count?: number;
  upload_date?: string;
  status?: string;
}

export interface DocumentMetadata {
  title: string;
  filename: string;
  file_size: number;
  file_type: string;
  page_count?: number;
  headers?: string[];
  chunk_count?: number;
}
