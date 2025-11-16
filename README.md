# Dev Guide Analyzer

FastAPI backend + Vite React (TypeScript) frontend to analyze code and generate reports. This README covers local development and Docker Compose setup to run both services together.

## Prerequisites
- Docker Desktop
- Node `>=20`
- Python `>=3.11` (only if developing without Docker)

## Run with Docker Compose
```bash
docker compose up --build
```
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`

Stop containers:
```bash
docker compose down
```

### Environment Variables (optional)
Create a `.env` in the project root if you want external AI fixes:
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (default `google/gemini-2.0-flash-exp:free`)
- `GOOGLE_API_KEY`
- `GOOGLE_MODEL` (default `gemini-1.5-flash`)

The frontend proxy target is controlled by `VITE_BACKEND_URL`. Compose sets it to `http://backend:8000` so browser calls to `/api/...` work automatically.

## Local Development (without Docker)
Backend (FastAPI):
```bash
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend (Vite React):
```bash
npm ci
npm run dev
```
- Vite dev server runs at `http://localhost:8080`.
- The proxy for `/api` is defined in `vite.config.ts` and uses `process.env.VITE_BACKEND_URL` (falls back to `http://127.0.0.1:8000`).

## Project Structure
- `backend/` — FastAPI app (`main.py`), `requirements.txt`, `Dockerfile`
- `src/` — React app code
- `Dockerfile` — Frontend (Vite dev server)
- `docker-compose.yml` — Runs frontend and backend together
- `vite.config.ts` — Vite server config and `/api` proxy

## NPM Scripts
- `npm run dev` — Start Vite dev server
- `npm run build` — Production build (outputs to `dist/`)
- `npm run preview` — Preview `dist/`

## API Endpoints (Backend)
- `GET /api/health` — Health check
- `GET /api/status` — AI keys configuration status
- `POST /api/analyze` — Analyze code and return score, issues, metrics
- `POST /api/report` — Text report for download
- `POST /api/report/html` — HTML report for download

## Troubleshooting
- Port in use: change ports in `vite.config.ts` or compose file.
- CORS: backend allows `http://localhost:8080` (and `5173`); adjust in `main.py` if needed.
- If frontend cannot reach the backend in Docker, ensure `VITE_BACKEND_URL` points to `http://backend:8000` (set by compose).

## Production Notes
- Current Docker setup runs the Vite dev server. For production, use a multi-stage build to `npm run build` and serve the static assets via `vite preview` or Nginx. If you want, we can add a production Dockerfile and compose profile.


## Project info

**URL**: https://lovable.dev/projects/e79af65c-2fd3-49eb-818f-f73eb8919b44

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/e79af65c-2fd3-49eb-818f-f73eb8919b44) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/e79af65c-2fd3-49eb-818f-f73eb8919b44) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
