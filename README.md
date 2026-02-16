# Sharp MX-B468F Printer Emulator

A full-stack microservices application that emulates a Sharp network printer's web management interface for safe testing of printer provisioning scripts without physical hardware.

## Purpose

This emulator was built to:
- Test printer configuration scripts in a sandboxed environment
- Validate SMTP settings with real authentication before deploying to production
- Demonstrate security-conscious architecture for enterprise IT automation

## Architecture

**Microservices Design:**
- **Frontend**: React UI (Port 5173) - Emulates Sharp printer web interface
- **Backend**: Python FastAPI (Port 8000) - Performs real SMTP validation

**Security Features:**
- Separation of concerns (UI and sensitive operations isolated)
- Real SMTP authentication testing
- No credentials stored in frontend
- CORS protection
- Input validation

## Quick Start

### Prerequisites
- Docker Desktop installed
- Git

### Run the Emulator
```bash
# Clone the repository
git clone https://github.com/yourusername/sharp-printer-emulator.git
cd sharp-printer-emulator

# Start both containers
docker-compose up --build

# Access the emulator
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Default Login:**
- Username: `admin`
- Password: `admin`

## Testing SMTP Configuration

1. Log in to the web interface
2. Fill in SMTP settings (Gateway, Port, Credentials)
3. Click "Test REAL Connection"
4. Backend performs actual SMTP authentication
5. View detailed results

**Supported SMTP Servers:**
- Gmail (smtp.gmail.com:587)
- Office 365 (smtp.office365.com:587)
- Any standard SMTP server

## Project Structure
```
sharp-emulator/
├── backend/              # Python FastAPI service
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── src/                  # React frontend
│   ├── App.jsx
│   └── main.jsx
├── docker-compose.yml    # Orchestrates both services
├── Dockerfile           # Frontend container
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind CSS config
└── README.md
```

## Development

**Hot Reload Enabled**

Edit files locally and see changes instantly:
- Frontend: Edit `src/App.jsx` and browser auto-refreshes
- Backend: Edit `backend/main.py` and API auto-restarts

**View Logs:**
```bash
# Frontend logs
docker logs sharp-printer-emulator --follow

# Backend logs
docker logs sharp-smtp-validator --follow
```

**Stop Services:**
```bash
docker-compose down
```

## Security Considerations

- Never use production credentials in test environments
- Backend validates all inputs before SMTP connections
- CORS restricted to localhost during development
- Credentials never logged or persisted
- SSRF protection through input validation
- Rate limiting recommended for production deployments

## Use Cases

- **IT Operations**: Test printer provisioning scripts safely
- **DevOps**: Develop automation without hardware dependencies
- **Security Testing**: Validate configurations before production deployment
- **Training**: Learn printer management without production risk

## Troubleshooting

**Containers won't start:**
```bash
docker-compose down
docker-compose up --build
```

**Hot reload not working (Windows):**
- Already configured with polling in `vite.config.js`

**Port conflicts:**
- Change ports in `docker-compose.yml` if 5173 or 8000 are in use

**Check container status:**
```bash
docker ps
```

## Technical Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Infrastructure**: Docker, Docker Compose
- **SMTP**: Python smtplib with SSL/TLS support

## API Documentation

Once running, view interactive API documentation at:
- Swagger UI: http://localhost:8000/docs

## License

MIT License - Feel free to use for learning and development

## Author

Built to demonstrate microservices architecture, security-first design principles, Docker containerization best practices, and full-stack development capabilities.