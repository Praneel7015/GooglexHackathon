<<<<<<< Updated upstream
# GooglexHackathon
=======
# NammaCity - Civic Operating System for Bangalore

Multi-agent AI civic OS: photograph any civic issue, auto-route to the right agency, bundle similar nearby complaints, escalate automatically, track on a public dashboard.

## Stack

- **Backend:** Python 3.12 + FastAPI
- **Agents:** Google ADK + Gemini 2.5 Pro
- **DB:** Supabase (PostgreSQL + PostGIS)
- **Vector DB:** Qdrant Cloud
- **Frontend:** React + Vite + Tailwind (PWA)
- **Maps:** Leaflet.js + OpenStreetMap

## Backend Setup

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn main:app --reload
```

## Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Project Settings > API** and copy your URL and `anon` key
3. Paste them into `backend/.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   ```
4. Go to **SQL Editor** in the Supabase dashboard
5. Paste the contents of `backend/db/schema.sql` and click **Run**
6. Seed the database:
   ```bash
   cd backend
   source venv/bin/activate
   python db/seed.py
   ```

## Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```
>>>>>>> Stashed changes
