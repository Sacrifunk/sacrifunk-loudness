"""Optional SMTP send for a Markdown report.

Credentials are read from environment variables — never from CLI args, never
hardcoded. Compatible with Gmail / Workspace SMTP (port 587 STARTTLS) and
classic 465 SSL providers.

Required env vars:
  SMTP_HOST       e.g. smtp.gmail.com
  SMTP_USER       e.g. info@sacrifunk.com
  SMTP_PASS       app password / token
  SMTP_FROM       From: header value (defaults to SMTP_USER)
Optional env vars:
  SMTP_PORT       default 587
  SMTP_SECURITY   "starttls" (default) | "ssl" | "none"
"""

from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional


class SMTPConfigError(RuntimeError):
    """Raised when required SMTP env vars are missing."""


@dataclass
class SMTPConfig:
    host: str
    port: int
    user: str
    password: str
    sender: str
    security: str  # "starttls" | "ssl" | "none"


def _load_config() -> SMTPConfig:
    missing = [k for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS") if not os.environ.get(k)]
    if missing:
        raise SMTPConfigError(f"missing env vars: {', '.join(missing)}")

    security = os.environ.get("SMTP_SECURITY", "starttls").lower()
    if security not in {"starttls", "ssl", "none"}:
        raise SMTPConfigError(f"SMTP_SECURITY must be starttls|ssl|none, got: {security}")

    return SMTPConfig(
        host=os.environ["SMTP_HOST"],
        port=int(os.environ.get("SMTP_PORT", "587")),
        user=os.environ["SMTP_USER"],
        password=os.environ["SMTP_PASS"],
        sender=os.environ.get("SMTP_FROM") or os.environ["SMTP_USER"],
        security=security,
    )


def send_report(
    *,
    to: str,
    subject: str,
    markdown_body: str,
    html_body: Optional[str] = None,
    config: Optional[SMTPConfig] = None,
) -> dict:
    """Send a report via SMTP. Returns metadata dict on success.

    Raises SMTPConfigError if env vars missing, or any smtplib exception bubbles up.
    """
    cfg = config or _load_config()

    msg = EmailMessage()
    msg["From"] = cfg.sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(markdown_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    if cfg.security == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg.host, cfg.port, context=context) as server:
            server.login(cfg.user, cfg.password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(cfg.host, cfg.port) as server:
            if cfg.security == "starttls":
                context = ssl.create_default_context()
                server.starttls(context=context)
            server.login(cfg.user, cfg.password)
            server.send_message(msg)

    return {
        "ok": True,
        "to": to,
        "from": cfg.sender,
        "subject": subject,
        "host": cfg.host,
        "port": cfg.port,
        "security": cfg.security,
        "size_bytes": len(markdown_body.encode("utf-8")),
    }
