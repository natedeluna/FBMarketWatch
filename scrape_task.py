import json
import time
from termcolor import colored
import sys
import re
from random import random, randint, uniform
from listings_builder import ListingsBuilder
from email_util import EmailDispatcher
import asyncio

class ScrapeTask:
    def __init__(self, browser_instance:any, page:any, query:dict):     
        self.marketplace_url = (
            f'https://www.facebook.com/marketplace/{query["fb_url_area_code"]}/search/?'
            f'query={query["search_phrase"]}&'
            f'daysSinceListed=1&'
            f'sortBy=creation_time_descend&'
            f'minPrice=500&'
            f'maxPrice={query["max_price"]}&'
        )
        
        self.query = query
        
        self.browser = browser_instance
        
        self.page = page

        self.select = self.load_class_selectors()

        print(colored(f"Scanning for {self.query['search_phrase']}", 'cyan'))

    async def run(self):
        await self.page.goto(self.marketplace_url, wait_until='networkidle')

        if await self.check_for_immediate_login_reroute():
            sys.exit(1)

        await self.initial_login_popup_exit()

        if self.query["search_radius"] > 40:
            await self.set_search_radius()

            await self.check_for_mini_login_popup()

        if self.query["should_scroll"]:
            await self.scroll_to_load_more_results()

        html = await self.page.content()

        listings_builder  = ListingsBuilder(html, self.select)

        listings_builder.get_raw_listings()

        listings_builder.update_existing_listings()
        
        listings_builder.remove_old_listings()
        
        listings_builder.filter_out_keywords()

        sanitized_new_listings = listings_builder.build()
        
        print(colored(f"=={len(sanitized_new_listings)}== new listings", 'green'))

        if len(sanitized_new_listings)>0 and len(sanitized_new_listings)<8:
            final_listings = await self.get_listing_times(sanitized_new_listings)

            if len(final_listings) > 0:
                email_dispatcher = EmailDispatcher(final_listings)

                await email_dispatcher.run()
        
    async def get_listing_times(self, listings:dict):
        pattern = r'\b(a minute ago|2 minutes ago|3 minutes ago|4 minutes ago|5 minutes ago|6 minutes ago|7 minutes ago|8 minutes ago|seconds ago)\b'
        keys_to_delete = []

        for key, value in listings.items():
            await self.page.goto(value["post_url"], wait_until='networkidle')

            post_meta_section_selectors = self.format_for_query_selector(self.select["listing_page_meta_section"])
            meta_section = await self.page.wait_for_selector(post_meta_section_selectors)

            time_submitted_selectors = self.format_for_query_selector(self.select["listing_page_time_submitted"])
            time_submitted_el = await meta_section.query_selector(time_submitted_selectors)
            
            if time_submitted_el is not None:
                time_submitted:str = await time_submitted_el.text_content()

                print((colored(f'Posted {time_submitted}','light_green')))

                if re.search(pattern, time_submitted):
                    print(colored('-adding-', 'light_grey'))

                    listings[key]["time_submitted"]= time_submitted
                else:
                    keys_to_delete.append(key)

        for key in keys_to_delete:
            del listings[key]

        return listings

    async def check_for_mini_login_popup(self):
        pop_up_class_selectors = self.format_for_query_selector(self.select["mini_login_popup_exitable"])
        
        if await self.page.query_selector(pop_up_class_selectors) is not None:
            exit_popup_selectors = self.format_for_query_selector(self.select["mini_login_popup_exitable_exit"])
            
            pop_up_el = await self.page.wait_for_selector(pop_up_class_selectors)
            
            exit_element = await pop_up_el.wait_for_selector(exit_popup_selectors)
            
            await exit_element.click()

    async def check_for_login_hard_block(self):
        pop_up_class_selectors = self.format_for_query_selector(self.select["login_popup_unexitable"])

        if await self.page.query_selector(pop_up_class_selectors) is not None:
            return True
            
        return False
    
    async def initial_login_popup_exit(self):
        login_popup_class_selectors = self.format_for_query_selector(self.select["login_popup_exitable"])

        hasPopup = await self.page.query_selector(login_popup_class_selectors)
        if hasPopup:
            time.sleep(1)
            exit_popup_selectors = self.format_for_query_selector(self.select["login_popup_exit"])

            await self.page.click(exit_popup_selectors)

            print(colored("Initial login popup exited", 'magenta'))

    async def scroll_to_load_more_results(self):
        viewport_size = self.page.viewport_size

        x_pos = int(viewport_size['width'] * 5 / 6)
        y_pos = int(viewport_size['height'] / 2)

        await self.page.mouse.move(x_pos, y_pos)

        time.sleep(randint(2,4))

        start_time = time.time()
        
        scroll_duration = randint(12, 17)

        print(colored(f"Scrolling for {scroll_duration} seconds", 'magenta'))

        while time.time() - start_time < scroll_duration:
            scroll_distance = randint(69, 111)
            sleep_time = uniform(0.1, 0.6)

            if random() < 0.03:
                scroll_distance = -scroll_distance 

            last_scroll_position = await self.page.evaluate('window.scrollY')
                
            await self.page.mouse.wheel(0, scroll_distance)

            time.sleep(sleep_time)
            
            new_scroll_position = await self.page.evaluate('window.scrollY')

            if last_scroll_position == new_scroll_position and scroll_distance > 0:
                print(colored(f'Reached end of page after {time.time() - start_time} seconds', 'magenta'))
                break
            elif await self.check_for_login_hard_block():
                break

    async def set_search_radius(self):
        time.sleep(randint(1, 3))

        search_radius_class_selectors = self.format_for_query_selector(self.select["search_radius_input"])

        try:
            search_radius = await self.page.wait_for_selector(search_radius_class_selectors)

            await search_radius.click()

            time.sleep(2)

            await self.check_for_mini_login_popup()

            for _ in range(10):
                await self.page.keyboard.press('Tab')
                focused_element = await self.page.evaluate(
                    '''() => {
                    const element = document.activeElement;
                    return element.innerText}'''
                )
                    
                await self.page.wait_for_timeout(randint(100, 444))
                
                if "Radius" in focused_element:
                    await self.page.keyboard.press('Enter')
                    await self.check_for_mini_login_popup()
                    break
            
            for _ in range(11):
                await self.page.keyboard.press('ArrowDown')
                await self.page.wait_for_timeout(randint(100, 444))

            await self.page.keyboard.press('ArrowUp')
            await self.page.wait_for_timeout(randint(50, 250))
            await self.page.keyboard.press('Enter')
            await self.page.wait_for_timeout(2000)

            await self.check_for_mini_login_popup()

            for _ in range(10):
                await self.page.keyboard.press('Tab')

                focused_element = await self.page.evaluate(
                    '''() => {
                        const element = document.activeElement;
                        return element.innerText}'''
                )

                await self.check_for_mini_login_popup()
                
                if focused_element == 'Apply':
                    await self.page.keyboard.press('Enter')
                    time.sleep(2)
                    await self.check_for_mini_login_popup()
                    break
        
            print(colored("Search radius set", 'magenta'))
        except Exception as e:
            return e

    def format_for_query_selector(self, input_string):
        return "." + input_string.replace(" ", ".")
    
    async def check_for_immediate_login_reroute(self):
        class_selectors = self.format_for_query_selector(self.select["immediate_login_reroute"])
        return await self.page.query_selector(class_selectors) is not None

    def load_class_selectors(self):
        with open("fbm_class_selectors.json", "r") as file:
            data = json.load(file)
            return data