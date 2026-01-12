# Chat With Your Docs

A modern RAG (Retrieval-Augmented Generation) chat application that lets you chat with your documents using multiple LLM providers.

## Features

- **Multi-Model Support**: Choose from HuggingFace (free), OpenAI, Anthropic, or Google models
- **RAG with Contextual Retrieval**: Advanced document retrieval using hybrid search (semantic + lexical)
- **Document Management**: Upload and manage PDF, DOCX, PPTX, and CSV files
- **Streaming Responses**: Real-time streaming chat responses
- **Session Management**: Save and resume conversations
- **Source Citations**: See which documents were used to generate responses

## Tech Stack

- **Backend**: FastAPI + LangChain + ChromaDB
- **Frontend**: Next.js 15 + Vercel AI SDK + shadcn/ui
- **Vector DB**: ChromaDB with HNSW indexing
- **Deployment**: Railway (backend) + Vercel (frontend)

## Supported Models

| Provider | Model | Required Env Key |
|----------|-------|------------------|
| HuggingFace (default) | Mixtral 8x7B | `HF_API_KEY` |
| OpenAI | GPT-5 Mini | `OPENAI_API_KEY` |
| Anthropic | Claude 4.5 Haiku | `ANTHROPIC_API_KEY` |
| Google | Gemini 3 Flash | `GEMINI_API_KEY` |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### 1. Clone the repository

```bash
git clone https://github.com/bharatr21/chat-with-your-docs.git
cd chat-with-your-docs
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start the backend

**Option A: Using uv (recommended)**

```bash
cd backend
uv sync  # Install dependencies from pyproject.toml
uv run fastapi dev app/main.py
```

**Option B: Using pip**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .  # Install from pyproject.toml
python -m uvicorn app.main:app --reload
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the app

Visit [http://localhost:3000](http://localhost:3000)

## Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Variables

### Backend

| Variable | Description | Required |
|----------|-------------|----------|
| `DEFAULT_HF_API_KEY` | Default HuggingFace API key for free tier | Yes |
| `HF_API_KEY` | User's HuggingFace API key | No |
| `OPENAI_API_KEY` | OpenAI API key | No |
| `ANTHROPIC_API_KEY` | Anthropic API key | No |
| `GEMINI_API_KEY` | Google Gemini API key | No |
| `CHROMA_DB_PATH` | Path to ChromaDB storage | No (default: `./chroma_db`) |
| `SESSION_STORAGE` | Storage type: `file` or `supabase` | No (default: `file`) |
| `CORS_ORIGINS` | Allowed CORS origins | No (default: `http://localhost:3000`) |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |

## API Endpoints

### Chat
- `POST /api/chat` - Streaming chat with RAG

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document
- `DELETE /api/documents/{id}` - Delete document

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions` - List sessions
- `GET /api/sessions/{id}` - Get session
- `DELETE /api/sessions/{id}` - Delete session

### Models
- `GET /api/models` - List available models

## Deployment

### Backend (Railway)

1. Create a new Railway project
2. Connect your GitHub repository
3. Set root directory to `backend`
4. Add environment variables
5. Railway auto-deploys on push

### Frontend (Vercel)

1. Import project to Vercel
2. Set root directory to `frontend`
3. Add `NEXT_PUBLIC_API_URL` environment variable
4. Deploy

## Future Roadmap

- [ ] vLLM integration for faster local inference
- [ ] Supabase session storage
- [ ] Multi-user authentication
- [ ] Document collaboration
- [ ] Advanced RAG techniques (reranking, query expansion)

## License

MIT
