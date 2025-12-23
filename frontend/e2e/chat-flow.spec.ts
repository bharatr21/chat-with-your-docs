import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * End-to-end integration test for the full chat flow:
 * 1. Load the application
 * 2. Verify models are loaded from backend
 * 3. Upload a document
 * 4. Select the document
 * 5. Send a chat message
 * 6. Verify response is received
 */

test.describe('Chat with Documents - Full Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the application with models from backend', async ({ page }) => {
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('Chat with Your Docs');

    // Verify model selector is present and has loaded models
    const modelSelector = page.locator('text=Model').locator('..');
    await expect(modelSelector).toBeVisible();

    // Click to open model dropdown
    await page.getByRole('button', { name: /Mixtral|Select a model/i }).click();

    // Should see at least HuggingFace provider
    await expect(page.getByText('HUGGINGFACE')).toBeVisible();
  });

  test('should show empty document state initially', async ({ page }) => {
    await expect(page.getByText('No documents uploaded')).toBeVisible();
  });

  test('should upload a document and display it', async ({ page }) => {
    // Create a test file
    const testContent = 'This is a test document about artificial intelligence and machine learning.';
    const testFilePath = path.join(__dirname, 'test-document.txt');
    fs.writeFileSync(testFilePath, testContent);

    try {
      // Upload the document
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Wait for upload to complete and document to appear
      await expect(page.getByText('test-document.txt')).toBeVisible({ timeout: 30000 });

      // Verify document shows in the list
      await expect(page.getByText(/TXT/)).toBeVisible();
    } finally {
      // Cleanup
      fs.unlinkSync(testFilePath);
    }
  });

  test('should enable chat input when document is selected', async ({ page }) => {
    // Create and upload a test file
    const testContent = 'Test content for enabling chat.';
    const testFilePath = path.join(__dirname, 'enable-chat-test.txt');
    fs.writeFileSync(testFilePath, testContent);

    try {
      // Upload document
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Wait for document to appear
      await expect(page.getByText('enable-chat-test.txt')).toBeVisible({ timeout: 30000 });

      // Initially, chat input should show "select documents" placeholder
      const chatInput = page.getByRole('textbox');

      // Select the document
      await page.getByText('enable-chat-test.txt').click();

      // Chat input should now be enabled with different placeholder
      await expect(chatInput).toHaveAttribute('placeholder', /ask a question/i);
      await expect(chatInput).not.toBeDisabled();
    } finally {
      fs.unlinkSync(testFilePath);
    }
  });

  test('full flow: upload, select, chat, receive response', async ({ page }) => {
    // Create a test document with specific content
    const testContent = `
      Machine Learning Basics

      Machine learning is a subset of artificial intelligence that enables
      computers to learn from data without being explicitly programmed.

      Key concepts include:
      - Supervised learning
      - Unsupervised learning
      - Reinforcement learning

      Neural networks are inspired by the human brain and consist of
      interconnected nodes that process information.
    `;
    const testFilePath = path.join(__dirname, 'ml-basics.txt');
    fs.writeFileSync(testFilePath, testContent);

    try {
      // Step 1: Upload document
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Wait for upload and processing
      await expect(page.getByText('ml-basics.txt')).toBeVisible({ timeout: 30000 });

      // Verify chunk count is shown (indicates processing completed)
      await expect(page.getByText(/chunks/)).toBeVisible({ timeout: 10000 });

      // Step 2: Select the document
      await page.getByText('ml-basics.txt').click();

      // Verify selection (should show "1 of 1 selected")
      await expect(page.getByText(/1 of 1 selected/)).toBeVisible();

      // Step 3: Send a chat message
      const chatInput = page.getByRole('textbox');
      await chatInput.fill('What is machine learning?');

      // Click send button
      await page.getByRole('button', { name: '' }).click(); // Send icon button

      // Step 4: Verify user message appears
      await expect(page.getByText('What is machine learning?')).toBeVisible();

      // Step 5: Wait for and verify assistant response
      // The response should mention something about the document content
      // Wait for loading indicator to disappear and response to appear
      await expect(page.locator('.animate-bounce')).toBeHidden({ timeout: 60000 });

      // There should be an assistant message (look for Bot icon or message content)
      const assistantMessages = page.locator('[class*="bg-muted"]').filter({ hasText: /.+/ });
      await expect(assistantMessages.first()).toBeVisible({ timeout: 30000 });

    } finally {
      fs.unlinkSync(testFilePath);
    }
  });

  test('should handle multiple document selection', async ({ page }) => {
    // Create two test files
    const file1Path = path.join(__dirname, 'doc1.txt');
    const file2Path = path.join(__dirname, 'doc2.txt');
    fs.writeFileSync(file1Path, 'First document content about Python programming.');
    fs.writeFileSync(file2Path, 'Second document content about JavaScript frameworks.');

    try {
      const fileInput = page.locator('input[type="file"]');

      // Upload first document
      await fileInput.setInputFiles(file1Path);
      await expect(page.getByText('doc1.txt')).toBeVisible({ timeout: 30000 });

      // Upload second document
      await fileInput.setInputFiles(file2Path);
      await expect(page.getByText('doc2.txt')).toBeVisible({ timeout: 30000 });

      // Select both documents
      await page.getByText('doc1.txt').click();
      await page.getByText('doc2.txt').click();

      // Verify both are selected
      await expect(page.getByText(/2 of 2 selected/)).toBeVisible();

      // Use "Select all" / "Deselect all" toggle
      await page.getByText('Deselect all').click();
      await expect(page.getByText(/0 of 2 selected/)).toBeVisible();

      await page.getByText('Select all').click();
      await expect(page.getByText(/2 of 2 selected/)).toBeVisible();

    } finally {
      fs.unlinkSync(file1Path);
      fs.unlinkSync(file2Path);
    }
  });

  test('should delete a document', async ({ page }) => {
    // Create and upload a test file
    const testFilePath = path.join(__dirname, 'delete-test.txt');
    fs.writeFileSync(testFilePath, 'Content to be deleted.');

    try {
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Wait for document to appear
      await expect(page.getByText('delete-test.txt')).toBeVisible({ timeout: 30000 });

      // Click the delete button (trash icon)
      const documentRow = page.getByText('delete-test.txt').locator('..');
      await documentRow.locator('button').last().click();

      // Document should be removed
      await expect(page.getByText('delete-test.txt')).not.toBeVisible();

      // Should show empty state again
      await expect(page.getByText('No documents uploaded')).toBeVisible();

    } finally {
      // File might already be cleaned up
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }
    }
  });

  test('should toggle sidebar', async ({ page }) => {
    // Sidebar should be visible initially
    await expect(page.getByText('Upload Documents')).toBeVisible();

    // Find and click the toggle button (chevron)
    const toggleButton = page.locator('button').filter({ has: page.locator('svg') }).first();

    // Look for the sidebar toggle specifically (positioned on the left edge)
    const sidebarToggle = page.locator('button:has(svg[class*="ChevronLeft"], svg[class*="lucide-chevron"])').first();

    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();

      // Sidebar content should be hidden
      await expect(page.getByText('Upload Documents')).not.toBeVisible();
    }
  });

  test('should switch between models', async ({ page }) => {
    // Open model selector
    await page.getByRole('button', { name: /Mixtral|Select a model/i }).click();

    // Should see provider groups
    await expect(page.getByText('HUGGINGFACE')).toBeVisible();

    // Select a different model if available
    const mixtralOption = page.getByText('Mixtral 8x7B');
    if (await mixtralOption.isVisible()) {
      await mixtralOption.click();

      // Dropdown should close and show selected model
      await expect(page.getByRole('button', { name: /Mixtral/i })).toBeVisible();
    }
  });
});
