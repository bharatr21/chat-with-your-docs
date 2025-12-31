# CI/CD Pipeline Documentation

## Overview

This GitHub Actions workflow runs critical tests on every push to `main` and `vercel` branches, and on pull requests to `main`. The pipeline is optimized to test core functionality without running all unit tests, ensuring fast feedback while maintaining quality.

## Pipeline Structure

The pipeline consists of 4 parallel/sequential jobs:

```
┌─────────────────┬─────────────────┐
│  Backend Tests  │ Frontend Tests  │  (Parallel)
└────────┬────────┴────────┬────────┘
         │                 │
         └────────┬────────┘
                  │
           ┌──────▼──────┐
           │  E2E Tests  │              (Sequential)
           └─────────────┘
                  │
           ┌──────▼──────┐
           │    Lint     │              (Parallel)
           └─────────────┘
```

## Jobs Description

### 1. Backend Tests (~60 tests)
Tests core backend functionality including:
- **API Endpoints** (`test_api_chat.py`, `test_api_documents.py`, `test_api_sessions.py`)
  - Chat endpoint with streaming responses
  - Document upload/delete operations
  - Session management

- **RAG Pipeline** (`test_rag_pipeline.py`)
  - Document retrieval and ranking
  - Context injection
  - Response generation

- **LLM Provider** (`test_llm_provider.py`)
  - Multi-provider support (HuggingFace, OpenAI, Anthropic, Google)
  - Model initialization
  - Streaming capabilities

- **Configuration** (`test_config.py`)
  - BYOK (Bring Your Own Key) architecture
  - Environment variable handling

**Not included:** Unit tests for individual components (metadata, document processor, session store, streaming utilities, RAG retriever, model registry) - these are covered by integration tests.

### 2. Frontend Tests (~30 tests)
Tests critical frontend components:
- **API Client** (`api.test.ts`) - Backend communication
- **ChatInterface** (`ChatInterface.test.tsx`) - Main chat component
- **DocumentUpload** (`DocumentUpload.test.tsx`) - File upload with validation
- **ModelSelector** (`ModelSelector.test.tsx`) - Model selection UI

**Not included:** Individual unit tests (MessageInput, MessageList, DocumentSelector, useDocuments, useModels, utils) - these are tested via integration tests or covered by E2E tests.

### 3. E2E Tests (~10 scenarios)
Full integration tests with Playwright covering:
- Application loading with models
- Document upload and display
- Multiple document selection
- Full chat flow (upload → select → chat → receive response)
- Document deletion
- Sidebar toggle
- Model switching

These tests run the actual application and verify end-to-end functionality.

### 4. Code Quality (Lint)
- **Backend**: Ruff linting
- **Frontend**: ESLint with Next.js config
- Runs as `continue-on-error` to not block deployment

## Test Selection Rationale

### Why not all 169 backend + 84 frontend tests?

**Speed vs Coverage Trade-off:**
- Running all 253 tests would slow down CI/CD significantly
- Selected 90-100 critical tests that cover main user flows
- E2E tests provide additional confidence for integration points

**What's excluded and why:**
1. **Unit tests covered by integration** - No need to test utilities when the integration tests verify the complete flow
2. **Component tests covered by E2E** - Playwright tests verify actual user interactions
3. **Redundant coverage** - Multiple test files testing the same underlying functionality

## GitHub Secrets Configuration

To enable full CI/CD functionality, add these secrets in GitHub:

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add the following secret:

| Secret Name | Description | Required? |
|-------------|-------------|-----------|
| `DEFAULT_HF_API_KEY` | HuggingFace API key for testing LLM functionality | Optional (uses 'test_key' fallback) |

**Note:** The workflow uses `|| 'test_key'` fallback, so tests will run without secrets but may skip actual LLM calls.

## Running Tests Locally

### Backend Tests (Critical)
```bash
cd backend
uv run pytest \
  tests/test_api_chat.py \
  tests/test_api_documents.py \
  tests/test_api_sessions.py \
  tests/test_rag_pipeline.py \
  tests/test_llm_provider.py \
  tests/test_config.py \
  -v
```

### Frontend Tests (Critical)
```bash
cd frontend
npx vitest run \
  src/lib/api.test.ts \
  src/components/chat/ChatInterface.test.tsx \
  src/components/documents/DocumentUpload.test.tsx \
  src/components/models/ModelSelector.test.tsx
```

### E2E Tests
```bash
cd frontend
npx playwright test
```

### All Tests (Full Suite)
```bash
# Backend (169 tests)
cd backend && uv run pytest

# Frontend (84 tests)
cd frontend && npm test -- --run
```

## Pipeline Performance

Estimated run times:
- **Backend Tests**: ~10-15 seconds
- **Frontend Tests**: ~5-10 seconds
- **E2E Tests**: ~2-3 minutes (includes server startup)
- **Lint**: ~10-15 seconds

**Total**: ~3-4 minutes per run

## Troubleshooting

### E2E Tests Failing
- Check Playwright report artifact in GitHub Actions
- Verify backend and frontend servers are starting correctly
- Ensure `DEFAULT_HF_API_KEY` is set if testing actual LLM calls

### Backend Tests Failing
- Check for missing environment variables
- Verify uv installation and Python 3.13 compatibility
- Review test logs for specific assertion failures

### Frontend Tests Failing
- Check Node.js version (should be 20)
- Verify all dependencies are installed
- Review for missing mocks or incorrect test setup

## Adding New Tests to CI/CD

When adding new critical functionality:

1. **Add integration/API tests** to the appropriate test file
2. **If adding a new critical component**, add its test file to the workflow:
   ```yaml
   run: |
     npx vitest run \
       src/lib/api.test.ts \
       src/components/new-critical-component.test.tsx \
       ...
   ```
3. **For E2E flows**, add scenarios to `frontend/e2e/chat-flow.spec.ts`

## Monitoring

View pipeline status:
- **Actions tab** in GitHub repository
- **Status badge** (can add to README):
  ```markdown
  ![CI/CD](https://github.com/<username>/<repo>/workflows/CI/CD%20Pipeline/badge.svg)
  ```
