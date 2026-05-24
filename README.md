# AdFlow — AI Marketing Platform

AI-powered marketing agency platform with automated content generation and client management.

## Features

- AI content generation powered by Claude (Anthropic) — posts, captions, campaigns
- Client portal with content calendar and approval workflow
- Multi-agent content pipeline per service type
- Social media publishing via Blotato API
- JWT authentication, role-based access (admin / client)
- 25 unit tests (pytest)

## Tech Stack

**Backend:** Python, FastAPI, PostgreSQL, SQLAlchemy  
**Frontend:** Next.js 15, TypeScript, Tailwind CSS  
**AI:** Claude API (Anthropic) — content generation  
**Publishing:** Blotato API  
**Deploy:** PM2, Uvicorn

## Project Structure

```
adflow/
├── backend/          # FastAPI app + PostgreSQL models
├── frontend/         # Next.js 15 app router
├── tests/            # 25 unit tests (pytest)
└── ecosystem.config.js  # PM2 config
```

## Setup

```bash
cp backend/.env.example backend/.env  # add API keys
bash start.sh
```

## Environment Variables

```
ANTHROPIC_API_KEY=your_key
DATABASE_URL=postgresql://...
SECRET_KEY=your_jwt_secret
BLOTATO_API_KEY=your_key
```

---

Built with FastAPI + Next.js 15 + Claude API
