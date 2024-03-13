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

    def loadQuerys(self):
        with open("query_instructions.json", "r") as file:
            data = json.load(file)
            return data["Trailers"]
        
    def load_proxy(self):
        # For now use royal residential
        return {
            'server': 'http://geo.iproyal.com:12321',
            'username': os.getenv('IPROYAL_USERNAME'),
            'password': os.getenv('IPROYAL_PASSWORD'),
        }

    async def run(self):
       async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, proxy=self.load_proxy())
            
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