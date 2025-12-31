"""
Document processing: parsing and chunking
"""

import os
from typing import Any

import docx2txt
import pypdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


class DocumentProcessor:
    """Process documents: parse and chunk"""

    SUPPORTED_TYPES = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
    }

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def is_supported(self, filename: str) -> bool:
        """Check if file type is supported"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.SUPPORTED_TYPES

    def extract_text(self, file_path: str, filename: str) -> tuple[str, dict[str, Any]]:
        """
        Extract text and metadata from document

        Returns:
            tuple: (text_content, metadata)
        """
        ext = os.path.splitext(filename)[1].lower()
        metadata = {
            "filename": filename,
            "file_type": self.SUPPORTED_TYPES.get(ext, "unknown"),
            "file_size": os.path.getsize(file_path),
        }

        if ext == ".pdf":
            text, pdf_metadata = self._extract_pdf(file_path)
            metadata.update(pdf_metadata)
        elif ext == ".docx":
            text, docx_metadata = self._extract_docx(file_path)
            metadata.update(docx_metadata)
        elif ext in [".txt", ".md", ".csv"]:
            text = self._extract_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return text, metadata

    def _extract_pdf(self, file_path: str) -> tuple[str, dict[str, Any]]:
        """Extract text from PDF"""
        text_parts = []
        metadata = {"headers": []}

        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                metadata["page_count"] = len(pdf_reader.pages)

                # Extract metadata
                if pdf_reader.metadata:
                    title = pdf_reader.metadata.get("/Title", "")
                    if title:
                        metadata["title"] = title

                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"[Page {page_num}]\n{page_text}")

        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}") from e

        return "\n\n".join(text_parts), metadata

    def _extract_docx(self, file_path: str) -> tuple[str, dict[str, Any]]:
        """Extract text from DOCX"""
        metadata = {}

        try:
            text = docx2txt.process(file_path)

            # Estimate page count (rough estimate: 500 words per page)
            word_count = len(text.split())
            metadata["page_count"] = max(1, word_count // 500)

        except Exception as e:
            raise ValueError(f"Error processing DOCX: {str(e)}") from e

        return text, metadata

    def _extract_text_file(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, encoding="latin-1") as file:
                return file.read()

    def chunk_text(self, text: str, metadata: dict[str, Any], doc_id: str) -> list[Document]:
        """
        Chunk text into smaller pieces

        Args:
            text: Full document text
            metadata: Document metadata
            doc_id: Document ID

        Returns:
            List of LangChain Document objects
        """
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)

        # Create Document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "doc_id": doc_id,
                "chunk_index": i,
                "chunk_total": len(chunks),
            }
            documents.append(Document(page_content=chunk, metadata=chunk_metadata))

        return documents

    def process_document(
        self, file_path: str, filename: str, doc_id: str
    ) -> tuple[list[Document], dict[str, Any]]:
        """
        Complete document processing pipeline

        Returns:
            tuple: (list of chunks, metadata)
        """
        # Extract text and metadata
        text, metadata = self.extract_text(file_path, filename)

        # Chunk text
        chunks = self.chunk_text(text, metadata, doc_id)

        # Update metadata with chunk count
        metadata["chunk_count"] = len(chunks)

        return chunks, metadata
