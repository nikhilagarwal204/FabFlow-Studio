# Tech Stack

## Frontend

- Next.js 16 (App Router, React 19)
- TypeScript with strict mode
- Tailwind CSS v4
- Radix UI primitives (via shadcn/ui pattern)
- Axios for API calls

## Backend

- FastAPI (Python)
- Pydantic + pydantic-settings for validation/config
- OpenAI SDK (GPT-4o with structured JSON output)
- HTTPX for async HTTP (FIBO API)
- FFmpeg for video compositing

## External Services

- OpenAI API: Storyboard generation
- Bria FIBO API: Image generation

## Common Commands

### Frontend (from `frontend/`)

```bash
npm run dev      # Start dev server (localhost:3000)
npm run build    # Production build
npm run lint     # ESLint
```

### Backend (from `backend/`)

```bash
# Activate venv first
source .venv/bin/activate

# Run dev server
uvicorn app.main:app --reload --port 8000

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

### Frontend (`frontend/.env.local`)

- `NEXT_PUBLIC_API_URL`: Backend API URL

### Backend (`backend/.env`)

- `OPENAI_API_KEY`: OpenAI API key
- `BRIA_API_KEY`: Bria FIBO API key
- `FRONTEND_URL`: CORS allowed origins
