'use client';

import { useState, useEffect } from 'react';
import { FileText, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentSelector } from '@/components/documents/DocumentSelector';
import { ModelSelector } from '@/components/models/ModelSelector';
import { useDocuments } from '@/hooks/useDocuments';
import { useModels } from '@/hooks/useModels';

export default function Home() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const {
    documents,
    isLoading: documentsLoading,
    uploadDocument,
    deleteDocument,
  } = useDocuments();

  const {
    groupedModels,
    models,
    isLoading: modelsLoading,
  } = useModels();

  // Set default model when models load
  useEffect(() => {
    if (models.length > 0 && !selectedModelId) {
      // Prefer HuggingFace model as default
      const defaultModel = models.find((m) => m.provider === 'HuggingFace') || models[0];
      setSelectedModelId(defaultModel.id);
    }
  }, [models, selectedModelId]);

  const handleUpload = async (file: File) => {
    await uploadDocument(file);
  };

  const handleDeleteDocument = async (id: string) => {
    await deleteDocument(id);
    setSelectedDocumentIds((prev) => prev.filter((docId) => docId !== id));
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`
          ${sidebarOpen ? 'w-80' : 'w-0'}
          transition-all duration-300 ease-in-out
          border-r bg-card overflow-hidden flex-shrink-0
        `}
      >
        <div className="w-80 h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b">
            <div className="flex items-center gap-2">
              <FileText className="w-6 h-6 text-primary" />
              <h1 className="text-lg font-semibold">Chat with Your Docs</h1>
            </div>
          </div>

          {/* Model Selector */}
          <div className="p-4 border-b">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Model</span>
            </div>
            <ModelSelector
              groupedModels={groupedModels}
              selectedModelId={selectedModelId}
              onModelChange={setSelectedModelId}
              isLoading={modelsLoading}
            />
          </div>

          {/* Document Upload */}
          <div className="p-4 border-b">
            <h2 className="text-sm font-medium mb-2">Upload Documents</h2>
            <DocumentUpload
              onUpload={handleUpload}
              isUploading={documentsLoading}
            />
          </div>

          {/* Document Selector */}
          <div className="flex-1 p-4 overflow-hidden flex flex-col">
            <h2 className="text-sm font-medium mb-2">Select Documents</h2>
            <div className="flex-1 overflow-y-auto">
              <DocumentSelector
                documents={documents}
                selectedIds={selectedDocumentIds}
                onSelectionChange={setSelectedDocumentIds}
                onDelete={handleDeleteDocument}
                isLoading={documentsLoading}
              />
            </div>
          </div>
        </div>
      </aside>

      {/* Sidebar Toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-card border rounded-r-lg p-1 hover:bg-muted transition-colors"
        style={{ left: sidebarOpen ? '320px' : '0' }}
      >
        {sidebarOpen ? (
          <ChevronLeft className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        <ChatInterface
          sessionId={sessionId}
          selectedDocumentIds={selectedDocumentIds}
          selectedModelId={selectedModelId}
        />
      </main>
    </div>
  );
}
