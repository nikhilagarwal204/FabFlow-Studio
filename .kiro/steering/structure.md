# Project Structure

```
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── page.tsx      # Main page (state machine: input → generating → complete)
│   │   │   ├── layout.tsx    # Root layout
│   │   │   └── globals.css   # Global styles + Tailwind
│   │   ├── components/
│   │   │   ├── ui/           # Reusable UI primitives (shadcn/ui pattern)
│   │   │   ├── VideoInputForm.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   ├── ParameterEditor.tsx
│   │   │   └── VideoPlayer.tsx
│   │   └── lib/
│   │       ├── api.ts        # Axios instance + API functions
│   │       ├── validation.ts # Input validation
│   │       └── utils.ts      # cn() helper
│   └── public/
│
├── backend/                  # FastAPI backend
│   └── app/
│       ├── main.py           # FastAPI app, routes, job management
│       ├── config.py         # Settings from env vars
│       ├── models.py         # Pydantic models (UserInput, Storyboard, Scene, Enhanced*)
│       ├── storyboard_generator.py  # OpenAI integration
│       ├── fibo_client.py    # Bria FIBO API client
│       ├── fibo_translator.py       # FIBO JSON translation
│       ├── frame_generator.py       # Frame generation service
│       ├── parameter_modification.py # Parameter modification for v2
│       └── video_compositor.py      # FFmpeg video assembly
```

## Conventions

- Frontend uses `@/` path alias for `src/`
- Backend models use snake_case; frontend uses camelCase
- UI components in `components/ui/` are generic primitives
- Feature components at `components/` root level
- Backend services follow lazy initialization pattern for API clients
- Jobs stored in-memory (prototype); use job_id for polling
- V1 API at `/api/*`, V2 enhanced API at `/api/v2/*`
