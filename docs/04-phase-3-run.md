# PinnacleOS local run (Phase 3)

```bash
docker compose up --build
```

- Founder console: http://localhost:3001  
  (mapped to 3001 because 3000 was already taken on this machine)
- API: http://localhost:8000/v1/health

**Without Google OAuth:** Desk → Load Tuesday inbox → Inbox and Audit.

**With Google:** create an OAuth web client with redirect  
`http://localhost:8000/v1/oauth/google/callback`,  
set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`, restart `api`, then Connect Gmail.

Scopes are **read-only**. The connector raises if send or calendar-write is attempted. Approving a draft returns 403 until Phase 4.
