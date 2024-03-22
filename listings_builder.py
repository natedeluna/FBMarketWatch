from bs4 import BeautifulSoup
from filelock import FileLock, Timeout
import json
import time
from termcolor import colored

class ListingsBuilder:
    def __init__(self, html:str, class_selectors:dict):
        self.html = html
        self.select = class_selectors
        self.raw_listings_total = 0

        self.raw_listings = {}
        self.new_listings = {}

    def get_raw_listings(self):
        soup = BeautifulSoup(self.html, 'html.parser')
        
        listings = soup.find_all("div", class_=self.select["listing_card_container"])

        for card in listings:
            if list(card.children):
                image_element = card.find('img', class_=self.select["listing_image"])
                image_url = image_element['src'] if image_element else None

                title_element = card.find('span', class_=self.select["listing_title"])
                title = title_element.text if title_element else None

                price_element = card.find('span', class_=self.select["listing_price"])
                price = price_element.text if price_element else None

                post_url_element = card.find('a', class_=self.select["listing_url"])
                post_url = post_url_element['href'] if post_url_element else None

                location_element = card.find('span', class_=self.select["listing_location"])
                location = location_element.text if location_element else None

                if all(v is not None for v in [title, price, post_url, location, image_url]):
                    self.raw_listings_total += 1
                    listing_key = str(title) + "||" + str(price)

                    self.raw_listings.update({
                        listing_key: {
                            "title": str(title),
                            "price": str(price),
                            "image_url": str(image_url),
                            "post_url": "https://www.facebook.com" + str(post_url),
                            "location": str(location),
                            "date_scraped": time.time()
                        }
                    })
        print(colored("Raw lisitngs total: " + str(self.raw_listings_total), 'light_green'))

    def filter_out_keywords(self):
        filtered_out_count = 0
        keywords = {
            'Chevy', 'chevy', 'Ford', 
            'ford', 'rental', 'Rental', 
            'Chevrolet', 'chevrolet', 'golf', 'Golf', 
            'Cart', 'cart', 'Mitsubishi', 'mitsubishi', 
            'dodge', 'Dodge', 'bike', 'Bike', 
            'jacket', 'Jacket', 'container', 'Container', 
            'truck', 'Truck', 'seadoo', 'Seadoo', 
            'Jetski', 'jetski', 'jet ski', 'Jet ski'}

        for key in list(self.new_listings.keys()):
            listing = self.new_listings[key]
            if any(word in listing["title"] for word in keywords):
                filtered_out_count += 1
                del self.new_listings[key]
    
    def update_existing_listings(self):
        lock = FileLock("listings.json.lock")
        try:
            with lock.acquire(timeout=10):
                with open('listings.json', 'r') as f:
                    existing_listings_store = json.load(f)
        except (FileNotFoundError, Timeout) as e:
            existing_listings_store = {}
            return e
        
        existing_listings_keys = set(existing_listings_store.keys())

        for key, value in self.raw_listings.items():
            if key not in existing_listings_keys:
                self.new_listings.update({key: value})
                existing_listings_store.update({key: value})

        try:
            with lock.acquire(timeout=10):
                with open('listings.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_listings_store, f, ensure_ascii=False, indent=4)
        except FileNotFoundError as e:
            return e

    def remove_old_listings(self):
        lock = FileLock("listings.json.lock")
        try:
            with lock.acquire(timeout=10):
                with open('listings.json', 'r') as file:
                    existing_listings_store = json.load(file)

                for key, value in existing_listings_store.items():
                    if time.time() - value["date_scraped"] > 4 * 86400:
                        del existing_listings_store[key]
                        print(colored(f"Deleted {key}", 'red'))

                with open('listings.json', 'w') as file:
                    json.dump(existing_listings_store, file, indent=4)

        except (FileNotFoundError, Timeout) as e:
            return e

    def build(self) -> dict:
        return self.new_listings