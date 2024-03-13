from bs4 import BeautifulSoup
from filelock import FileLock, Timeout
import json
import time

class ListingsBuilder:
    def __init__(self, html:str, class_selectors:dict):
        self.html = html
        self.select = class_selectors
        self.raw_listings_total = 0

        self.raw_listings = {}
        self.new_listings = {}

    def get_raw_listings(self):
        # Gets relevant lisitngs from html
        soup = BeautifulSoup(self.html, 'html.parser')
        
        relevant_listings_container = soup.find("div", class_=self.select["relevant_results_container"])
        listings = relevant_listings_container.find_all("div", class_=self.select["listing_card_container"])

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

    def filter_out_keywords(self):
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
                del self.new_listings[key]
    
    def check_against_existing_listings(self):
        # Sanitizes raw lisitngs down to only the new listings 
        lock = FileLock("listings.json.lock")
        try:
            with lock.acquire(timeout=10):
                with open('listings.json', 'r') as file:
                    existing_listings_store = json.load(file)

        except (FileNotFoundError, Timeout) as e:
            return e
        
        exisitng_listings_keys = existing_listings_store.keys()

        for key, value in self.raw_listings.items():
            if key not in exisitng_listings_keys:
                self.new_listings.update({key: value})

    def update_existing_listings(self):
        # Updates the existing listings.json store with the new listings
        lock = FileLock("listings.json.lock")
        try:
            with lock.acquire(timeout=10):
                with open('listings.json', 'r', encoding='utf-8') as f:
                    existing_listings = json.load(f)

                existing_listings.update(self.new_listings)

                with open('listings.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_listings, f, ensure_ascii=False, indent=4)

        except (FileNotFoundError, json.JSONDecodeError, Timeout) as e:
            return e

    def remove_old_listings(self):
        lock = FileLock("listings.json.lock")
        try:
            with lock.acquire(timeout=10):
                with open('listings.json', 'r') as file:
                    existing_listings_store = json.load(file)

                for key in list(existing_listings_store.keys()):
                    if key not in self.raw_listings.keys():
                        existing_listings_store.pop(key)

                with open('listings.json', 'w') as file:
                    json.dump(existing_listings_store, file, indent=4)

        except (FileNotFoundError, Timeout) as e:
            return e

    def build(self) -> dict:
        return self.new_listings