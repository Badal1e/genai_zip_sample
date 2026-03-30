import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

_LOG = logging.getLogger(__name__)

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def looks_like_email(value: str) -> bool:
    s = (value or "").strip()
    return bool(s and _EMAIL_RE.match(s))


def send_complaint_registered_email(
    to_addr: str,
    acknowledgement_number: str,
    customer_id: str,
    case_id: int,
) -> None:
    if os.getenv("EMAIL_ENABLED", "true").strip().lower() in ("0", "false", "no"):
        _LOG.info("EMAIL_ENABLED is off; skipping registration email")
        return

    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        _LOG.info("SMTP_HOST not set; skipping registration email")
        return

    if not to_addr or not looks_like_email(to_addr):
        _LOG.info("Invalid recipient; skipping registration email")
        return

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()

    if not user or not password:
        _LOG.warning("SMTP_USER or SMTP_PASSWORD missing; cannot send email")
        return

    use_yagmail = os.getenv("SMTP_USE_YAGMAIL", "true").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    from_addr = os.getenv("SMTP_FROM", user).strip() or user

    subject = f"Complaint registered — {acknowledgement_number}"
    body = (
        "Hello,\n\n"
        "Your complaint has been registered.\n\n"
        f"Acknowledgement number: {acknowledgement_number}\n"
        f"Customer ID: {customer_id}\n"
        f"Case reference: #{case_id}\n\n"
        "We will email you again when your case is approved or rejected.\n"
    )

    try:
        _send_one(
            host,
            port,
            user,
            password,
            from_addr,
            to_addr.strip(),
            subject,
            body,
            use_yagmail,
        )
    except Exception:
        _LOG.exception("Failed to send complaint registration email")


def _build_customer_body(payload: dict) -> tuple[str, str]:
    verdict = payload.get("verdict", "")
    case_id = payload.get("case_id", "")
    txn = payload.get("transaction_id", "")
    ack = (payload.get("acknowledgement_number") or "").strip()
    summary = (payload.get("ai_summary") or "")[:1500]

    subject = f"Your dispute case #{case_id} — {verdict}"
    body = (
        "Hello,\n\n"
        f"This is an update about your dispute (case #{case_id}).\n\n"
        f"Status: {verdict}\n"
    )
    if ack:
        body += f"Acknowledgement number: {ack}\n"
    body += (
        f"Customer ID: {payload.get('customer_id') or '—'}\n"
        f"Transaction ID: {txn}\n\n"
    )
    if summary:
        body += f"Summary:\n{summary}\n\n"
    body += (
        "If you have questions, reply to this message or contact support using your case ID.\n"
    )
    return subject, body


def _send_via_yagmail(
    host: str,
    port: int,
    user: str,
    password: str,
    to_addr: str,
    subject: str,
    body: str,
) -> None:
    import yagmail

    if port == 465:
        with yagmail.SMTP(
            user,
            password,
            host=host,
            port=port,
            smtp_ssl=True,
            smtp_starttls=False,
        ) as yag:
            yag.send(to=to_addr, subject=subject, contents=body)
    else:
        with yagmail.SMTP(
            user,
            password,
            host=host,
            port=port,
            smtp_ssl=False,
        ) as yag:
            yag.send(to=to_addr, subject=subject, contents=body)


def _send_via_smtplib(
    host: str,
    port: int,
    user: str,
    password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> None:
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))
    raw = msg.as_string()

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=45) as server:
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], raw)
    else:
        with smtplib.SMTP(host, port, timeout=45) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], raw)


def _send_one(
    host: str,
    port: int,
    user: str,
    password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    use_yagmail: bool,
) -> None:
    if use_yagmail:
        try:
            _send_via_yagmail(host, port, user, password, to_addr, subject, body)
            _LOG.info("Email sent to %s (yagmail)", to_addr)
            return
        except Exception:
            _LOG.exception("yagmail send failed for %s; trying smtplib", to_addr)
    _send_via_smtplib(host, port, user, password, from_addr, to_addr, subject, body)
    _LOG.info("Email sent to %s (smtplib)", to_addr)


def send_verdict_email(payload: dict) -> None:
    """Send verdict only to the customer email on the dispute (e.g. manual entry). No admin copy."""
    if os.getenv("EMAIL_ENABLED", "true").strip().lower() in ("0", "false", "no"):
        _LOG.info("EMAIL_ENABLED is off; skipping verdict email")
        return

    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        _LOG.info("SMTP_HOST not set; skipping verdict email")
        return

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()

    if not user or not password:
        _LOG.warning("SMTP_USER or SMTP_PASSWORD missing; cannot send email")
        return

    cust = (payload.get("customer_email") or "").strip()
    if not cust or not looks_like_email(cust):
        _LOG.info("No valid customer_email on case; skipping verdict email")
        return

    use_yagmail = os.getenv("SMTP_USE_YAGMAIL", "true").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    from_addr = os.getenv("SMTP_FROM", user).strip() or user

    cust_subject, cust_body = _build_customer_body(payload)
    try:
        _send_one(
            host,
            port,
            user,
            password,
            from_addr,
            cust,
            cust_subject,
            cust_body,
            use_yagmail,
        )
    except Exception:
        _LOG.exception("Failed to send customer verdict email")
