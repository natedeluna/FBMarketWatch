import asyncio
import aiosmtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from filelock import FileLock, Timeout
from dotenv import load_dotenv
import os
from termcolor import colored

load_dotenv()
class EmailDispatcher:
    def __init__(self, listings:dict):
        self.recipients = self.load_recipient_emails()
        self.listings = listings
        self.email_body = self.generate_html_email()
    
    def load_recipient_emails() -> list:
        lock = FileLock("recipients.txt.lock")
        try:
            with lock.acquire(timeout=10):
                with open('recipients.txt', 'r') as file:
                    return file.read().splitlines()
        except (Timeout, FileNotFoundError) as e:
            return []

    async def run(self):
        email_client_index = 0

        for recipient in self.recipients:
            env_email_client_user = os.getenv(f"OUTLOOK_CLIENT_EMAIL{email_client_index}")
            env_email_client_password = os.getenv(f"OUTLOOK_CLIENT_PASSWORD{email_client_index}")

            email_client_user = env_email_client_user if env_email_client_user else os.getenv(f"OUTLOOK_CLIENT_EMAIL{email_client_index-1}")
            email_client_password = env_email_client_password if env_email_client_password else os.getenv(f"OUTLOOK_CLIENT_PASSWORD{email_client_index-1}")

            await self.send_email(
                email_client_user,
                email_client_password,
                recipient,
            )

            email_client_index += 1

    async def send_email(
        self, 
        email_client_user:str,
        email_client_password:str,
        email_recipient:str,
    ):
        subject = f"New Facebook Marketplace Listing(s)"
        # Set up the SMTP server.
        smtp_server = "smtp-mail.outlook.com"
        port = 587  # For starttls
        username = email_client_user
        password = email_client_password
        to_email_main = email_recipient
        # to_email_cc = "na14de@gmail.com"

        # Create the email.
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email_main
        # msg['Cc'] = to_email_cc
        msg['Subject'] = subject
        msg.attach(MIMEText(self.email_body, 'html'))
        msg.add_header('X-Priority', '1')
        msg.add_header('Importance', 'High')
        msg.add_header('X-MSMail-Priority', 'High')


        # Send the email.
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(username, password)
        text = msg.as_string()
        # cc_addresses = [to_email_cc]
        all_recipients = [msg['To']]

        res = server.sendmail(username, all_recipients, text)

        if not res == {}:
            print(colored('Error sending email', 'red'))
            print(colored(res, 'red'))
        else:
            print(colored('==EMAILED LISTINGS==', 'green'))

        server.quit()

    def generate_html_email(self):
        body_html = ''

        for key,value in self.listings.items():
            body_html += """
            <div style="margin-bottom: 100px;">
                <img src="{image_url}" style="width: 50%;">
                <h3>{price}</h3>
                <h4 style="font-weight: normal; color: green;">{time_submitted}</h4>
                <a href="{post_url}" style="color: blue;">{title}</a>
                <br>
            </div>
            """.format(image_url=value["image_url"], price=value["price"], title=value["title"], location=value["location"], post_url=value["post_url"], time_submitted=value["time_submitted"])

        self.email_body = body_html
