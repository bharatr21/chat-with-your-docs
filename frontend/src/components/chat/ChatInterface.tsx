'use client';

import { useChat } from '@ai-sdk/react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

interface ChatInterfaceProps {
  sessionId: string;
  selectedDocumentIds: string[];
  selectedModelId: string;
}

export function ChatInterface({
  sessionId,
  selectedDocumentIds,
  selectedModelId,
}: ChatInterfaceProps) {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`,
    body: {
      session_id: sessionId,
      document_ids: selectedDocumentIds,
      model_id: selectedModelId,
    },
    onError: (error) => {
      console.error('Chat error:', error);
    },
  });

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} isLoading={isLoading} />
      <MessageInput
        input={input}
        handleInputChange={handleInputChange}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        disabled={selectedDocumentIds.length === 0}
      />
    </div>
  );
}
