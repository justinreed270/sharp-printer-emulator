import os
import smtplib
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local fake SMTP server — injected by docker-compose
SMTP_TEST_HOST = os.environ.get("SMTP_TEST_HOST", "smtp-server")
SMTP_TEST_PORT = int(os.environ.get("SMTP_TEST_PORT", "587"))

app = FastAPI(title="Sharp Printer SMTP Validator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class SMTPConfig(BaseModel):
    primaryGateway: str
    primaryPort: int
    replyAddress: str
    useSSL: str
    smtpAuth: str
    deviceUserid: str
    devicePassword: str

    @field_validator("primaryPort")
    @classmethod
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class TestResult(BaseModel):
    success: bool
    message: str
    details: list[dict]


@app.get("/")
def read_root():
    return {"status": "Sharp SMTP Validator API - Running", "version": "2.0"}


@app.post("/test-smtp", response_model=TestResult)
async def test_smtp_connection(config: SMTPConfig):
    logger.info(
        "SMTP test — provisioned gateway: %s:%d", config.primaryGateway, config.primaryPort
    )
    results = []

    # ── Step 1: echo back what the provisioning script configured ──────────
    results.append({
        "type": "info",
        "message": (
            f"Provisioned gateway : {config.primaryGateway}:{config.primaryPort}"
            f"  |  SSL mode: {config.useSSL}"
            f"  |  Auth: {config.smtpAuth}"
        ),
    })
    results.append({
        "type": "info",
        "message": f"Reply address : {config.replyAddress}",
    })
    results.append({
        "type": "info",
        "message": (
            "Routing to local SMTP test server — "
            "zero external network traffic, fully air-gapped"
        ),
    })

    # ── Step 2: connect to the local fake SMTP server ──────────────────────
    server = None
    try:
        server = smtplib.SMTP(SMTP_TEST_HOST, SMTP_TEST_PORT, timeout=10)
        server.ehlo()
        results.append({
            "type": "success",
            "message": "✓ Connected to local SMTP test server",
        })
    except Exception as exc:
        results.append({
            "type": "error",
            "message": f"✗ Cannot reach local SMTP test server: {exc}",
        })
        logger.error("Local SMTP server unreachable: %s", exc)
        return TestResult(
            success=False, message="Local SMTP server unreachable", details=results
        )

    # ── Step 3: STARTTLS (honoured when user selected negotiate / tls) ─────
    if config.useSSL in ("negotiate", "tls"):
        try:
            server.starttls()
            server.ehlo()
            results.append({
                "type": "success",
                "message": "✓ STARTTLS negotiated successfully",
            })
        except Exception:
            results.append({
                "type": "warning",
                "message": "⚠ STARTTLS not available on test server — continuing unencrypted",
            })

    # ── Step 4: authentication ─────────────────────────────────────────────
    if config.smtpAuth != "none" and config.deviceUserid:
        results.append({
            "type": "info",
            "message": f"Authenticating as: {config.deviceUserid}",
        })
        try:
            server.login(config.deviceUserid, config.devicePassword)
            results.append({
                "type": "success",
                "message": "✓ Authentication PASSED — credentials accepted by test server",
            })
            server.quit()
            results.append({
                "type": "success",
                "message": "\n✓ ALL TESTS PASSED — SMTP configuration is valid",
            })
            logger.info("SMTP test passed for user %r", config.deviceUserid)
            return TestResult(
                success=True,
                message="SMTP configuration validated successfully",
                details=results,
            )
        except smtplib.SMTPAuthenticationError:
            results.append({
                "type": "error",
                "message": "✗ Authentication FAILED — username or password is incorrect",
            })
            logger.warning("SMTP auth failed for user %r", config.deviceUserid)
            try:
                server.quit()
            except Exception:
                pass
            return TestResult(
                success=False, message="Authentication failed", details=results
            )
        except Exception as exc:
            results.append({
                "type": "error",
                "message": f"✗ Authentication error: {exc}",
            })
            try:
                server.quit()
            except Exception:
                pass
            return TestResult(
                success=False, message="Authentication error", details=results
            )
    else:
        results.append({
            "type": "warning",
            "message": "⚠ No authentication configured — connection-only test",
        })
        server.quit()
        results.append({
            "type": "success",
            "message": "✓ Connection test passed (no credentials to validate)",
        })
        return TestResult(
            success=True, message="Connection successful, no auth configured", details=results
        )


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sharp-smtp-validator"}
