# MuelaADS

Marketing agency platform with AI-powered content generation.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- PM2 (`npm install -g pm2`)

### Setup

1. Configure environment:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

2. Create PostgreSQL database:
   ```sql
   CREATE DATABASE muelaads;
   CREATE USER muelaads WITH PASSWORD 'muelaads';
   GRANT ALL PRIVILEGES ON DATABASE muelaads TO muelaads;
   ```

3. Start the platform:
   ```bash
   bash start.sh
   ```

4. Open http://localhost:3000

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `BLOTATO_API_KEY` | From blotato.com/dashboard |

### Development

Backend only:
```bash
uvicorn backend.main:app --reload --port 8000
```

Frontend only:
```bash
cd frontend && npm run dev
```

Run tests:
```bash
python -m pytest tests/ -v
```
