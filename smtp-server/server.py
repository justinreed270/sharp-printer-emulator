"""
Fake SMTP server for Sharp Printer Emulator.

Validates credentials against SMTP_VALID_USER / SMTP_VALID_PASSWORD env vars.
All mail is silently discarded — nothing ever leaves this container.
"""

import asyncio
import os
import ssl
import logging

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, LoginPassword

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [smtp-server] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

VALID_USER = os.environ.get("SMTP_VALID_USER", "printer@local.test")
VALID_PASSWORD = os.environ.get("SMTP_VALID_PASSWORD", "changeme")
PORT = int(os.environ.get("SMTP_PORT", "587"))


class Authenticator:
    def __call__(self, server, session, envelope, mechanism, auth_data):
        if not isinstance(auth_data, LoginPassword):
            logger.warning("Auth FAILED: unexpected auth data type %s", type(auth_data))
            return AuthResult(success=False, handled=True)

        username = auth_data.login.decode("utf-8", errors="replace")
        password = auth_data.password.decode("utf-8", errors="replace")
        logger.info("Auth attempt: mechanism=%s user=%r", mechanism, username)

        if username == VALID_USER and password == VALID_PASSWORD:
            logger.info("Auth SUCCESS for user %r", username)
            return AuthResult(success=True)

        logger.warning("Auth FAILED: wrong credentials for user %r", username)
        return AuthResult(success=False, handled=True)


class DiscardHandler:
    """Accept the SMTP session but silently discard every message."""

    async def handle_DATA(self, server, session, envelope):
        logger.info(
            "Message discarded from=%r to=%r",
            envelope.mail_from,
            envelope.rcpt_tos,
        )
        return "250 Message accepted (discarded — this is a test server)"


async def run():
    # Attempt to load the self-signed cert generated at image build time.
    # STARTTLS is offered but NOT required (auth_require_tls=False) so that
    # clients that skip TLS still get a proper auth response.
    tls_context = None
    cert_path = "/app/cert.pem"
    key_path = "/app/key.pem"
    if os.path.exists(cert_path) and os.path.exists(key_path):
        try:
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls_context.load_cert_chain(cert_path, key_path)
            logger.info("TLS certificate loaded — STARTTLS is available")
        except Exception as exc:
            tls_context = None
            logger.warning("Could not load TLS cert (%s) — STARTTLS disabled", exc)
    else:
        logger.info("No TLS cert found — running plain SMTP only")

    controller = Controller(
        DiscardHandler(),
        hostname="0.0.0.0",
        port=PORT,
        authenticator=Authenticator(),
        auth_required=True,
        auth_require_tls=False,
        tls_context=tls_context,
    )
    controller.start()

    logger.info("Fake SMTP server listening on port %d", PORT)
    logger.info("Accepted user: %r", VALID_USER)
    logger.info("No mail is ever sent or stored — fully air-gapped")

    await asyncio.Event().wait()  # run until killed


if __name__ == "__main__":
    asyncio.run(run())
