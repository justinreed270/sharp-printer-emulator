from fastapi.responses import HTMLResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
import smtplib
import ssl
from email.mime.text import MIMEText
import socket
import ipaddress
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SSRF protection: block connections to private/reserved IP ranges
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),    # loopback
    ipaddress.ip_network("10.0.0.0/8"),      # RFC 1918 private
    ipaddress.ip_network("172.16.0.0/12"),   # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918 private
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("100.64.0.0/10"),   # CGNAT shared space
    ipaddress.ip_network("0.0.0.0/8"),       # unspecified
    ipaddress.ip_network("::1/128"),         # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),        # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),       # IPv6 link-local
]


def _is_blocked_ip(ip: str) -> bool:
    """Return True if the IP falls in a private/reserved range (SSRF guard)."""
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in _BLOCKED_NETWORKS)
    except ValueError:
        return True  # unparseable address → block

app = FastAPI(title="Sharp Printer SMTP Validator")

# Enable CORS so React can call this API
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
    replyAddress: str  # Changed from EmailStr to str for flexibility
    useSSL: str
    smtpAuth: str
    deviceUserid: str
    devicePassword: str

    @field_validator('primaryPort')
    @classmethod
    def validate_port(cls, v):
        if not isinstance(v, int):
            raise ValueError('Port must be an integer')
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

class TestResult(BaseModel):
    success: bool
    message: str
    details: list[dict]

@app.get("/")
def read_root():
    return {"status": "Sharp SMTP Validator API - Running", "version": "1.0"}

@app.post("/test-smtp", response_model=TestResult)
async def test_smtp_connection(config: SMTPConfig):
    """
    Test actual SMTP connection with provided credentials
    """
    logger.info(f"Testing SMTP connection to {config.primaryGateway}:{config.primaryPort}")
    results = []
    
    try:
        # Step 1: Validation
        results.append({
            "type": "info",
            "message": f"Testing connection to {config.primaryGateway}:{config.primaryPort}..."
        })
        
        # Step 2: DNS Resolution
        try:
            resolved_ip = socket.gethostbyname(config.primaryGateway)
            results.append({
                "type": "success",
                "message": f"✓ DNS resolution successful: {config.primaryGateway} -> {resolved_ip}"
            })
        except socket.gaierror as e:
            results.append({
                "type": "error",
                "message": f"✗ Cannot resolve hostname: {config.primaryGateway}"
            })
            logger.error(f"DNS resolution failed: {e}")
            return TestResult(success=False, message="DNS resolution failed", details=results)

        # SSRF guard: reject private/reserved IPs before opening any connection
        if _is_blocked_ip(resolved_ip):
            results.append({
                "type": "error",
                "message": f"✗ Hostname resolves to a private/reserved IP ({resolved_ip}) — connection blocked"
            })
            logger.warning(f"SSRF attempt blocked: {config.primaryGateway} -> {resolved_ip}")
            return TestResult(
                success=False,
                message="SSRF protection: target IP is not permitted",
                details=results
            )

        # Step 3: Connection Test
        results.append({
            "type": "info",
            "message": f"Attempting connection to port {config.primaryPort}..."
        })
        
        try:
            # Determine SSL/TLS mode
            if config.useSSL == "ssl" or config.primaryPort == 465:
                # Direct SSL connection
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config.primaryGateway, config.primaryPort, timeout=10, context=context)
                results.append({
                    "type": "success",
                    "message": "✓ Connected using SSL/TLS (port 465)"
                })
            else:
                # STARTTLS or plain
                server = smtplib.SMTP(config.primaryGateway, config.primaryPort, timeout=10)
                server.ehlo()
                results.append({
                    "type": "success",
                    "message": "✓ Connected to SMTP server"
                })
                
                if config.useSSL in ["negotiate", "tls"]:
                    try:
                        server.starttls()
                        server.ehlo()
                        results.append({
                            "type": "success",
                            "message": "✓ STARTTLS negotiation successful"
                        })
                    except Exception as e:
                        results.append({
                            "type": "warning",
                            "message": f"⚠ STARTTLS failed: {str(e)}"
                        })
            
            # Step 4: Authentication Test
            if config.smtpAuth != "none" and config.deviceUserid and config.devicePassword:
                results.append({
                    "type": "info",
                    "message": f"Attempting authentication as {config.deviceUserid}..."
                })
                
                try:
                    server.login(config.deviceUserid, config.devicePassword)
                    results.append({
                        "type": "success",
                        "message": "✓ Authentication successful!"
                    })
                    
                    results.append({
                        "type": "success",
                        "message": "✓ SMTP account is ready to send emails"
                    })
                    
                except smtplib.SMTPAuthenticationError as e:
                    results.append({
                        "type": "error",
                        "message": f"✗ Authentication failed: Invalid username or password"
                    })
                    logger.error(f"SMTP auth failed: {e}")
                    server.quit()
                    return TestResult(success=False, message="Authentication failed", details=results)
                except Exception as e:
                    results.append({
                        "type": "error",
                        "message": f"✗ Authentication error: {str(e)}"
                    })
                    logger.error(f"Auth error: {e}")
                    server.quit()
                    return TestResult(success=False, message="Authentication error", details=results)
            else:
                results.append({
                    "type": "warning",
                    "message": "⚠ No authentication configured - skipping auth test"
                })
            
            # Clean up
            server.quit()
            
            results.append({
                "type": "success",
                "message": "\n✓ ALL TESTS PASSED! SMTP configuration is valid and working."
            })
            
            logger.info("SMTP test completed successfully")
            return TestResult(
                success=True,
                message="SMTP connection test successful",
                details=results
            )
            
        except smtplib.SMTPConnectError as e:
            results.append({
                "type": "error",
                "message": f"✗ Cannot connect to {config.primaryGateway}:{config.primaryPort}"
            })
            logger.error(f"Connection error: {e}")
            return TestResult(success=False, message="Connection failed", details=results)
            
        except socket.timeout:
            results.append({
                "type": "error",
                "message": "✗ Connection timeout - server not responding"
            })
            logger.error("Connection timeout")
            return TestResult(success=False, message="Connection timeout", details=results)
            
        except Exception as e:
            results.append({
                "type": "error",
                "message": f"✗ Connection error: {str(e)}"
            })
            logger.error(f"Unexpected error: {e}")
            return TestResult(success=False, message=f"Connection error: {str(e)}", details=results)
    
    except Exception as e:
        results.append({
            "type": "error",
            "message": f"✗ Unexpected error: {str(e)}"
        })
        logger.error(f"Fatal error: {e}")
        return TestResult(success=False, message=f"Test failed: {str(e)}", details=results)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sharp-smtp-validator"}