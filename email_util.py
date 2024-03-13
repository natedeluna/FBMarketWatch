import asyncio
import aiosmtplib
from email.message import EmailMessage
from filelock import FileLock, Timeout
from dotenv import load_dotenv

load_dotenv()
class EmailDispatcher:
    def __init__(self, listings:dict):
        self.recipients = self.load_recipient_email()
        self.listings = listings
    
    def load_recipient_email():
        lock = FileLock("recipients.txt.lock")
        try:
            with lock.acquire(timeout=10):
                with open('recipients.txt', 'r') as file:
                    return file.read().splitlines()
        except (Timeout, FileNotFoundError) as e:
            return e

    async def run(self):
        self.generate_html_email()

    def generate_html_email(self):
        

    async def send_email(self, recipient, listing):
        message = EmailMessage()
