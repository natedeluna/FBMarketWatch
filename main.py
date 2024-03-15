from threading import Lock
from random import random, randint, uniform, choice
import os
from dotenv import load_dotenv
from termcolor import colored
from playwright.async_api import async_playwright
import json
import asyncio
from scrape_task import ScrapeTask

file_lock = Lock()

load_dotenv()
class Browser:
    def __init__(self, name):
        self.querys = self.loadQuerys()

        self.name = name
        self.lock = file_lock
        self.browser_config = {
            "headless": False,
            "proxy": "royal_residential",
        }

    def loadQuerys(self):
        with open("query_instructions.json", "r") as file:
            data = json.load(file)
            return data["Trailers"]
        
    def parse_ip(env_var_value: str) -> dict:
        ip_address, port, username, password = env_var_value.split(":")
        return {
            "ip_address": ip_address,
            "port": port,
            "username": username,
            "password": password
        }

    def load_proxy(self):
        # For now use royal residential
        if self.browser_config["proxy"] == "royal_residential":
            return {
                'server': 'http://geo.iproyal.com:12321',
                'username': os.getenv('IPROYAL_USERNAME'),
                'password': os.getenv('IPROYAL_PASSWORD'),
            }

        else:
            parsed_ips = [self.parse_ip(os.getenv(f"RESIDENTIAL_IP{i}")) for i in range(1, 10) if os.getenv(f"RESIDENTIAL_IP{i}")]
            selected_ip = choice(parsed_ips)
            return  {
                'server': f'http://{selected_ip["ip_address"]}:{selected_ip["port"]}',
                'username': selected_ip["username"],
                'password': selected_ip["password"],
            }

    async def run(self):
       async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.browser_config["headless"], proxy=self.load_proxy())
            
            screen_size = p.devices['Desktop Chrome']['viewport']
            
            context = await browser.new_context(viewport=screen_size)

            page = await context.new_page()

            for query in self.querys:
                await context.clear_cookies()
                task = ScrapeTask(context, page, query)
                await task.run()

            await browser.close()

    


# ************START***************
MAIN_THREAD = Browser("Main")
asyncio.run(MAIN_THREAD.run())
# ********************************