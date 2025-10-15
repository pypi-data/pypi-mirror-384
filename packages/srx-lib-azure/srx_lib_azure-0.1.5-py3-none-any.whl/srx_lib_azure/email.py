import os
import logging
from typing import Dict, Any

try:
    from azure.communication.email.aio import EmailClient
except Exception:  # pragma: no cover - optional dependency at import time
    EmailClient = None  # type: ignore

logger = logging.getLogger(__name__)


class EmailService:
    """Thin wrapper over Azure Communication Services EmailClient.

    Does not raise on missing configuration to keep the library optional.
    If not configured, send calls are skipped with a warning and a 'skipped' status.
    """

    def __init__(self):
        self.connection_string = os.getenv("ACS_CONNECTION_STRING")
        self.sender_address = os.getenv("EMAIL_SENDER")
        if not self.connection_string or not self.sender_address or EmailClient is None:
            self.email_client = None
            logger.warning(
                "EmailService not configured (missing ACS_CONNECTION_STRING/EMAIL_SENDER or azure SDK). Calls will be skipped."
            )
        else:
            try:
                self.email_client = EmailClient.from_connection_string(self.connection_string)
            except Exception as e:
                self.email_client = None
                logger.warning("EmailService initialization failed: %s", e)

    async def send_notification(self, recipient: str, subject: str, body: str, html: bool = False) -> Dict[str, Any]:
        if not self.email_client or not self.sender_address:
            logger.warning("Email skipped: service not configured")
            return {"status": "skipped", "message": "Email service not configured"}
        message = {
            "content": {"subject": subject},
            "recipients": {"to": [{"address": recipient}]},
            "senderAddress": self.sender_address,
        }
        if html:
            message["content"]["html"] = body
        else:
            message["content"]["plainText"] = body
        try:
            poller = await self.email_client.begin_send(message)
            result = await poller.result()
            message_id = result.get("id")
            if message_id:
                logger.info("Email sent to %s with Message ID: %s", recipient, message_id)
                return {"status": "success", "message": "Email sent successfully", "message_id": message_id}
            logger.error("Failed to send email. Result: %s", result)
            return {"status": "error", "message": f"Failed to send email: {result}"}
        except Exception as e:
            logger.error("Email send exception: %s", e)
            return {"status": "error", "message": str(e)}
