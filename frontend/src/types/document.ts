export interface DocumentMetadata {
  title: string;
  filename: string;
  file_size: number;
  file_type: string;
  page_count?: number;
  headers?: string[];
  chunk_count?: number;
}

export interface Document {
  id: string;
  metadata: DocumentMetadata;
}
