# Sharp MX-B468F Printer Emulator

A full-stack microservices application that emulates the Sharp MX-B468F printer's web management interface — built to safely test and validate printer provisioning scripts without touching production hardware.

## Why This Exists

Enterprise IT teams that manage fleets of network printers face a real problem: there's no sandbox. Provisioning scripts have to be validated somewhere, and "somewhere" is usually a production printer. A misconfigured SMTP relay means scan-to-email breaks across an entire building. A bad credential means a support call. Testing in production isn't a workflow — it's a liability.

This project solves that by providing a locally-running emulator that behaves like a real Sharp printer web interface, backed by a Python service that performs genuine SMTP authentication against real mail servers. You get real test results without real risk.

## Architecture

Two containers. One responsibility each.

```
┌─────────────────────────────────────────────────────┐
│                   Docker Network                    │
│                                                     │
│  ┌──────────────────┐      ┌──────────────────────┐ │
│  │  Frontend        │      │  Backend             │ │
│  │  React + Vite    │──-──▶│  Python FastAPI      │ │
│  │  Port 5173       │      │  Port 8000           │ │
│  │                  │      │                      │ │
│  │  Emulates Sharp  │      │  Real SMTP testing   │ │
│  │  web interface   │      │  DNS resolution      │ │
│  └──────────────────┘      │  Auth validation     │ │
│                            └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Why two containers instead of one?**

The split is intentional. The frontend handles UI rendering and user interaction — work that belongs in the browser context. The backend handles outbound network connections and credential validation — work that must never happen client-side. Keeping these separate means credentials are never exposed in frontend code, the backend can be locked down independently, and each service can be updated or replaced without touching the other. This mirrors how you'd architect any production system where sensitive operations need to be isolated from the presentation layer.

**Why FastAPI for the backend?**

FastAPI gives you automatic input validation via Pydantic models, async support for network I/O (important when you're making real SMTP connections that may time out), and built-in OpenAPI documentation at `/docs`. For a service that takes structured input and makes outbound connections, it's the right tool. Flask would work but requires more boilerplate to get the same validation guarantees.

**Why React + Vite for the frontend?**

The Sharp printer web interface is a form-heavy UI. React's component model maps cleanly to that — each configuration section is a self-contained component with its own state. Vite keeps the development loop fast with hot module replacement, which matters when you're iterating on UI layout to match real printer behavior.

## Security Design Decisions

**Credentials never touch the frontend.** The React app collects SMTP credentials from the user and posts them to the backend API. The backend performs authentication. Credentials are never logged, never stored, and never returned to the client. This reflects how real enterprise systems handle sensitive data — the UI is a dumb form, the backend is the trust boundary.

**Separation of concerns as a security control.** By isolating the SMTP connection logic in the backend container, the attack surface for credential exposure is minimized. Even if the frontend were compromised, it has no access to the SMTP credentials after they're submitted.

**Known gap — SSRF mitigation.** The backend currently accepts any hostname as the SMTP gateway and attempts a connection. This is appropriate for a sandboxed development tool but would require input validation before production use — specifically an allowlist of permitted SMTP hosts and a denylist of internal IP ranges (RFC 1918, localhost, link-local). This is a documented future enhancement, not an oversight.

**CORS.** Currently set to allow all origins for development convenience. A production deployment would restrict this to the specific frontend origin.

## Quick Start

### Prerequisites
- Docker Desktop

### Run
```bash
git clone https://github.com/justinreed270/sharp-printer-emulator.git
cd sharp-printer-emulator
docker-compose up --build
```

**Frontend:** http://localhost:5173  
**Backend API:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs  

**Default credentials:** admin / admin

## How the SMTP Test Works

When you click "Test REAL Connection," the frontend POSTs your configuration to the backend `/test-smtp` endpoint. The backend then:

1. Validates input via Pydantic model (port range, required fields)
2. Resolves the SMTP hostname via DNS — confirms the server exists
3. Opens a TCP connection to the specified host and port
4. Negotiates TLS via STARTTLS if configured
5. Attempts authentication with the provided credentials
6. Returns a structured result with pass/fail status for each step

This gives you the same signal a real printer would get when it tries to send a scan — before you've touched a single production device.

## Project Structure

```
sharp-printer-emulator/
├── backend/
│   ├── Dockerfile
│   ├── main.py           # FastAPI service — SMTP validation logic
│   └── requirements.txt
├── src/
│   ├── App.jsx           # React frontend — printer UI emulation
│   └── main.jsx
├── docker-compose.yaml   # Service orchestration
├── Dockerfile            # Frontend container
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Development

**Hot reload is enabled for both services.**

Edit `src/App.jsx` — browser refreshes automatically.  
Edit `backend/main.py` — API restarts automatically.

```bash
# View logs
docker logs sharp-printer-emulator --follow
docker logs sharp-smtp-validator --follow

# Stop
docker-compose down
```

## Companion Project

This emulator is designed to be tested against the [Sharp Automation Script](https://github.com/justinreed270/sharp-automation) — a Selenium-based provisioning tool that drives this interface the same way it would drive a real printer's web management page.

Together they demonstrate a full provisioning pipeline: automation script → emulator → validated SMTP config → production deployment.

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | React, Vite, Tailwind CSS | Component model fits form-heavy UI; fast dev loop |
| Backend | Python 3.11, FastAPI, Uvicorn | Input validation, async I/O, auto-generated API docs |
| SMTP | Python smtplib | Standard library, full SSL/TLS/STARTTLS support |
| Infrastructure | Docker, Docker Compose | Reproducible environments; mirrors production deployment patterns |

## License

MIT