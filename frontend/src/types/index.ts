export interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  document_count: number;
  message_count: number;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  num_chunks: number;
  status: "processing" | "ready" | "error";
  uploaded_at: string;
  error_message?: string | null;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  num_chunks: number;
  num_pages?: number | null;
  has_images: boolean;
  message: string;
}

export interface DocumentStatusResponse {
  document_id: string;
  status: string;
  num_chunks: number;
  error_message?: string | null;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_num?: number | null;
  chunk_text: string;
  relevance_score: number;
  has_image: boolean;
  image_path?: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[] | null;
  created_at: string;
}
