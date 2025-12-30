'use client';

import { useState, useEffect } from 'react';
import { APIKeys, getAPIKeys, saveAPIKeys, clearAPIKeys } from '@/lib/apiKeys';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Eye, EyeOff, Key, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ApiKeySettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ApiKeySettings({ open, onOpenChange }: ApiKeySettingsProps) {
  const [keys, setKeys] = useState<APIKeys>({});
  const [showKeys, setShowKeys] = useState({
    openai: false,
    anthropic: false,
    gemini: false,
    huggingface: false,
  });

  // Load keys from localStorage on mount
  useEffect(() => {
    if (open) {
      setKeys(getAPIKeys());
    }
  }, [open]);

  const handleSave = () => {
    saveAPIKeys(keys);
    onOpenChange(false);
    // Reload the page to fetch models with new keys
    window.location.reload();
  };

  const handleClear = () => {
    if (confirm('Are you sure you want to clear all API keys?')) {
      clearAPIKeys();
      setKeys({});
    }
  };

  const toggleVisibility = (provider: keyof typeof showKeys) => {
    setShowKeys(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            API Key Settings
          </DialogTitle>
          <DialogDescription>
            Add your own API keys to enable additional AI models. Keys are stored locally in your browser.
          </DialogDescription>
        </DialogHeader>

        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            Your API keys are stored only in your browser's local storage and sent directly to the backend.
            They are never logged or stored on the server.
          </AlertDescription>
        </Alert>

        <div className="space-y-4 py-4">
          {/* OpenAI */}
          <div className="space-y-2">
            <Label htmlFor="openai">OpenAI API Key</Label>
            <div className="flex gap-2">
              <Input
                id="openai"
                type={showKeys.openai ? 'text' : 'password'}
                placeholder="sk-..."
                value={keys.openai || ''}
                onChange={(e) => setKeys({ ...keys, openai: e.target.value })}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => toggleVisibility('openai')}
              >
                {showKeys.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="underline">platform.openai.com</a>
            </p>
          </div>

          {/* Anthropic */}
          <div className="space-y-2">
            <Label htmlFor="anthropic">Anthropic API Key</Label>
            <div className="flex gap-2">
              <Input
                id="anthropic"
                type={showKeys.anthropic ? 'text' : 'password'}
                placeholder="sk-ant-..."
                value={keys.anthropic || ''}
                onChange={(e) => setKeys({ ...keys, anthropic: e.target.value })}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => toggleVisibility('anthropic')}
              >
                {showKeys.anthropic ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your key at <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener noreferrer" className="underline">console.anthropic.com</a>
            </p>
          </div>

          {/* Google Gemini */}
          <div className="space-y-2">
            <Label htmlFor="gemini">Google Gemini API Key</Label>
            <div className="flex gap-2">
              <Input
                id="gemini"
                type={showKeys.gemini ? 'text' : 'password'}
                placeholder="AI..."
                value={keys.gemini || ''}
                onChange={(e) => setKeys({ ...keys, gemini: e.target.value })}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => toggleVisibility('gemini')}
              >
                {showKeys.gemini ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your key at <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline">makersuite.google.com</a>
            </p>
          </div>

          {/* HuggingFace */}
          <div className="space-y-2">
            <Label htmlFor="huggingface">HuggingFace API Key</Label>
            <div className="flex gap-2">
              <Input
                id="huggingface"
                type={showKeys.huggingface ? 'text' : 'password'}
                placeholder="hf_..."
                value={keys.huggingface || ''}
                onChange={(e) => setKeys({ ...keys, huggingface: e.target.value })}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => toggleVisibility('huggingface')}
              >
                {showKeys.huggingface ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your key at <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener noreferrer" className="underline">huggingface.co/settings</a>
            </p>
          </div>
        </div>

        <DialogFooter className="flex justify-between sm:justify-between">
          <Button type="button" variant="destructive" onClick={handleClear}>
            Clear All
          </Button>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={handleSave}>
              Save Keys
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
