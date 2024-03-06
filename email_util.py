import asyncio
import aiosmtplib
from email.message import EmailMessage

class EmailDispatcher:
    def __init__(self, recipients):
        self.recipients = recipients
    
    async def send_email(self, recipient, listing):
        message = EmailMessage()
