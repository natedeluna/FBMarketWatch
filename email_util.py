from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from filelock import FileLock, Timeout
from dotenv import load_dotenv
import os
from termcolor import colored

load_dotenv()
class EmailDispatcher:
    def __init__(self, listings:dict=None):
        self.recipients = self.load_recipient_emails()
        self.listings = listings
        self.email_body = None
    
    def load_recipient_emails(self) -> list:
        lock = FileLock("client_emails.txt.lock")
        try:
            with lock.acquire(timeout=10):
                with open('client_emails.txt', 'r') as file:
                    return file.read().splitlines()
        except (Timeout, FileNotFoundError) as e:
            return []

    async def run(self):
        self.generate_html_email()

        email_client_index = 0
        for recipient in self.recipients:
            email_client_user = os.getenv(f"OUTLOOK_CLIENT_EMAIL{email_client_index}")
            email_client_password = os.getenv(f"OUTLOOK_CLIENT_PASSWORD{email_client_index}")

            if email_client_user is None:
                email_client_index = 0
                email_client_user = os.getenv(f"OUTLOOK_CLIENT_EMAIL{email_client_index}")
                email_client_password = os.getenv(f"OUTLOOK_CLIENT_PASSWORD{email_client_index}")

            await self.send_email(
                email_client_user,
                email_client_password,
                recipient,
            )

            email_client_index += 1
        print(colored('==EMAILED ALL RECIPIENTS==', 'green'))

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

        if res:
            print(f"Failed to send email: {res}")

        print(colored(f'{email_client_user} =>> {email_recipient} ::sent','blue'))
        server.quit()

    def generate_html_email(self):
        if not self.listings:
            self.email_body = """<h1>Helloooo</h1>"""
            return

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