from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import time, datetime, pytz
from bs4 import BeautifulSoup
from fastapi import HTTPException, FastAPI
import json, requests
import uvicorn, sys
from termcolor import colored
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from logging.handlers import RotatingFileHandler
import random, asyncio, re
from random import random, randint, uniform, choice
from urllib.parse import quote
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def return_ip_information():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://www.ipburger.com/')
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        ip_address = soup.find('span', id='ipaddress1').text
        country = soup.find('strong', id='country_fullname').text
        location = soup.find('strong', id='location').text
        isp = soup.find('strong', id='isp').text
        hostname = soup.find('strong', id='hostname').text
        ip_type = soup.find('strong', id='ip_type').text
        version = soup.find('strong', id='version').text
        browser.close()
        return {
            'ip_address': ip_address,
            'country': country,
            'location': location,
            'isp': isp,
            'hostname': hostname,
            'type': ip_type,
            'version': version
        }

async def get_iproyal_balance():
    # FIX API REQ TO GET BALANCE
    url = "https://dashboard.iproyal.com/api/residential/royal/reseller/my-info"
    payload={}
    headers = {
        'X-Access-Token': os.getenv('IPROYAL_API_TOKEN')
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.text

async def scrape_through_listings (page, query, browser, scroll, expand_search_radius, p):
    if expand_search_radius == True:
        search_radius_selectors = '.x78zum5.xl56j7k.x1y1aw1k.x1sxyh0.xwib8y2.xurb0ha'
        try:
            search_radius = await page.wait_for_selector(search_radius_selectors)
        except Exception as e:
            print(colored(f"An error ocurred: {e}"))
            sys.exit(1)
            
            
        search_radisu_tc = await search_radius.text_content()
        if 'Within 250 miles' not in search_radisu_tc:
            await change_search_radius(search_radius, page)
            print(colored('Search radius set to 250 mi', 'cyan'))
            await check_for_mini_login_popup(page)
        else:
            print(colored('Search radius already set to 100 mi', 'cyan'))
    already_logged_count = False
    if scroll == True:
        time.sleep(randint(1,4))
        print(colored('Scrolling..', 'cyan'))
        start_time = time.time()
        scroll_duration = randint(12, 15)
        while time.time() - start_time < scroll_duration:
            scroll_distance = randint(69, 111)
            sleep_time = uniform(0.05, 0.5)
            if random() < 0.03:
                scroll_distance = -scroll_distance 
            await page.mouse.wheel(0, scroll_distance)
            time.sleep(sleep_time)
            if await check_for_login_hard_block(page):
                if query == 'Dump%20Trailer' and scroll == True:
                    log_listing_count(1)
                    already_logged_count = True
                break
                
            
        print(colored('Finished scrolling', 'green'))
        
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    parsed = {}
    top_level_listings_container = soup.find('div', class_='xkrivgy x1gryazu x1n2onr6')
    listings = top_level_listings_container.find_all('div', class_='x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24')
    total_found = 0
    for listing in listings:
        if not list(listing.children):
            print(listing)
            print(colored('has no children', 'red'))
            continue
        try:                   
            image_element = listing.find('img', class_='xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3')
            image_url = image_element['src'] if image_element else None

            # Finding a title element by its class and getting its text
            title_element = listing.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6')
            title = title_element.text if title_element else None

            # Finding a price element by its class and getting its text
            price_element = listing.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u')
            price = price_element.text if price_element else None

            # Finding a post URL element by its class and getting its 'href' attribute
            post_url_element = listing.find('a', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1lku1pv')
            post_url = post_url_element['href'] if post_url_element else None
            # Finding a location element by its class and getting its text
            location_element = listing.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft')
            location = location_element.text if location_element else None
            
            if all(v is not None for v in [title, price, post_url, location, image_url]):
                key = str(title) + "||" + str(price)
                parsed.update({
                    key: {
                        "title": str(title),
                        "price": str(price),
                        "image_url": str(image_url),
                        "post_url": "https://www.facebook.com" + str(post_url),
                        "location": str(location)
                    }
                })
                total_found = total_found + 1
            else:
                pass
        except Exception as e:
            print(f"An error occurred: {e}")
    
    remove_old_listings()
    print(colored(f'TOTAL LISTINGS SCRAPED - {total_found}', 'green'))
    
    if query == 'Dump%20Trailer' and scroll == True and already_logged_count == False:
        log_listing_count(total_found)
        
    
    # handles checking for listings already scraped and removing blacked out key words
    new_listings = update_new_listings(parsed)["data"]
    if (len(new_listings) > 0 and len(new_listings) < 8):
        browser_1 = await p.chromium.launch(headless=False)
        p2 = await browser_1.new_page()
        
        for key in list(new_listings.keys()):
            url = new_listings[key]["post_url"]
            await p2.goto(url)
            time_listed = await get_time_listed(p2)
            new_listings[key]["listed_time"] = str(time_listed)

        await browser_1.close()
        email_listings(new_listings, query)  
    else:
        if len(new_listings) == 0:
            print(colored('No new listings found','red'))
        elif len(new_listings) >= 5:
            print(colored(f'{len(listings)} listings found: catching up with backlog','red'))

    return True

async def get_time_listed(page):
    post_meta_section_sel = '.xyamay9.x1pi30zi.x18d9i69.x1swvt13'
    listing_time_sel = '.x1yztbdb'
    post_meta_section = await page.wait_for_selector(post_meta_section_sel)
    listing_time = await post_meta_section.query_selector(listing_time_sel)
    if listing_time:
        return await listing_time.text_content()
    else:
        return ''

async def change_search_radius(search_radius_element, page):
    await search_radius_element.click()
    print(colored('Clicked search radius', 'cyan'))
    time.sleep(2)
    await check_for_mini_login_popup(page)
    miles_input_selectors = '.xjyslct.xjbqb8w.x13fuv20.xu3j5b3.x1q0q8m5.x26u7qi.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.xzsf02u.x78zum5.x1jchvi3.x1fcty0u.x132q4wb.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x1a2a7pz.x9desvi.x1pi30zi.x1a8lsjc.x1swvt13.x1n2onr6.x16tdsg8.xh8yej3.x1ja2u2z'
    miles_input = await page.wait_for_selector(miles_input_selectors)
    await miles_input.click()
    print(colored('Clicked input menu', 'cyan'))
    for _ in range(10):
        await page.keyboard.press('ArrowDown')
        # Generate a random delay between 100 and 450 milliseconds
        random_delay = randint(100, 444)
        await page.wait_for_timeout(random_delay)  # Use the random delay
        

    time.sleep(1)
    await check_for_mini_login_popup(page)
    await page.keyboard.press('Enter')
    time.sleep(2)
    await check_for_mini_login_popup(page)
    
    for _ in range(10):
        await page.keyboard.press('Tab')
        focused_element = await page.evaluate('''() => {
                const element = document.activeElement;
                return element.innerText}''')

        await check_for_mini_login_popup(page)
        
        if focused_element == 'Apply':
            await page.keyboard.press('Enter')
            time.sleep(2)
            await check_for_mini_login_popup(page)
            break

def update_new_listings(scraped_data):
    try:
        with open('listings.json', 'r') as f:
            existing_data = json.load(f)
    except(FileNotFoundError,  json.JSONDecodeError):
        existing_data = {}
        return {"status": "error", "data": "Unable to open the listings.json file."}

    existing_keys = set(existing_data.keys())
    verified_new_listings = {}

    for key, data in scraped_data.items():
        if key in existing_keys:
            pass
        else:
            print(colored(f'New item found: {key}', 'green'))
            verified_new_listings.update({key: data})
            data.update({'date_added': time.time()})
            existing_data.update({key: data})
        
    if len(verified_new_listings) == 0:
        return {"status": "success", "data": {}}

    try:
        with open('listings.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False ,indent=4)
            print(colored('Listings database updated', 'green'))
    except(FileNotFoundError,  json.JSONDecodeError) as e:
        logging.error(f"Failed to open the listings.json file: {e}")
        return {"status": "error", "data": "Unable to open the listings.json file."}
    
    # After adding new listings to JSON, filter out blacked out keywords
    filter_out_key_words = {'Chevy', 'chevy', 'Ford', 'ford', 'rental', 'Rental', 'Chevrolet', 'chevrolet', 'golf', 'Golf', 'Cart', 'cart', 'Mitsubishi', 'mitsubishi', 'dodge', 'Dodge', 'bike', 'Bike', 'jacket', 'Jacket', 'container', 'Container', 'truck', 'Truck', 'seadoo', 'Seadoo', 'Jetski', 'jetski', 'jet ski', 'Jet ski'}
    
    for key in list(verified_new_listings.keys()):
        value = verified_new_listings[key]
        if any(keyword in value["title"] for keyword in filter_out_key_words):
            print(colored(f'Not emailing this listing: {value["title"]}', 'red'))
            del verified_new_listings[key]
    
    return {"status": "success", "data": verified_new_listings}

def remove_old_listings():
    try: 
        with open('listings.json', 'r') as f:
            existing_data = json.load(f)
    except(FileNotFoundError,  json.JSONDecodeError):
        return {"status": "error", "message": "Unable to open the listings.json file to remove old listings."}
    
    five_days_ago = time.time() - 432000
    keys_to_delete = [key for key, data in existing_data.items() if data["date_added"] < five_days_ago]
    
    items_removed = 0
    
    for key in keys_to_delete:
        items_removed = items_removed + 1
        del existing_data[key]

    print(colored(f'{items_removed} removed','red'))
    
    if keys_to_delete:
        try:
            with open('listings.json', 'w', encoding='utf-8') as f:
                print(colored('Updating the listings.json file.', 'green'))
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
        except(FileNotFoundError, json.JSONDecodeError):
            return {"status": "error", "message": "Unable to open the listings.json file to write new data"}

async def check_for_mini_login_popup(page):
    sel = '.x9f619.x78zum5.xl56j7k.x2lwn1j.xeuugli.x47corl.x1qjc9v5.x1bwycvy.x1e558r4.x150jy0e.x1x97wu9.xbr3nou.xqit15g.x1bi8yb4'
    hasPopup = await page.query_selector(sel) is not None
    if hasPopup:
        exit_popup_selectors = '.x1i10hfl.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x1ypdohk.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x16tdsg8.x1hl2dhg.xggy1nq.x87ps6o.x1lku1pv.x1a2a7pz.x6s0dn4.x14yjl9h.xudhj91.x18nykt9.xww2gxu.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x78zum5.xl56j7k.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1n2onr6.xc9qbxq.x14qfxbe.x1qhmfi1'

        pop_up_el = await page.wait_for_selector(sel)
        exit_element = await pop_up_el.wait_for_selector(exit_popup_selectors)
        await exit_element.click()
        print(colored('Exited popup','green'))

async def check_for_login_popup(page):
    print(colored('Checking for login popup','cyan'))
    sel = '.x1n2onr6.x1ja2u2z.x1afcbsf.x78zum5.xdt5ytf.x1a2a7pz.x6ikm8r.x10wlt62.x71s49j.x1jx94hy.x1qpq9i9.xdney7k.xu5ydu1.xt3gfkd.x104qc98.x1g2kw80.x16n5opg.xl7ujzl.xhkep3z.x193iq5w'
    hasPopup = await page.query_selector(sel)
    if hasPopup:
        time.sleep(1)
        exit_popup_selectors = '.x92rtbv.x10l6tqk.x1tk7jg1.x1vjfegm'
        await page.click(exit_popup_selectors)
        print(colored('exited login popup','green'))

async def check_for_login_hard_block(page):
    sel = '.x6s0dn4.x78zum5.x2lah0s.x1qughib.x879a55.x1n2onr6'
    hasPopup = await page.query_selector(sel) is not None

    if hasPopup:
        return True
    else:
        return False

async def check_for_immediate_login_reroute(page, selected_ip):
    sel = '._4-u5._30ny'
    hasEl = await page.query_selector(sel) is not None
    
    if hasEl:
        print(colored('Immediate login detected, ip not valid to use','cyan'))
        with open('faulty_ips.txt', 'r+') as file:
            faulty_ips = file.read().splitlines()

            if selected_ip not in faulty_ips:
                print(colored(f'Adding {selected_ip} to faulty_ips.txt', 'red'))
                file.write(selected_ip + '\n')

        sys.exit(1)
        
        return True
    else:
        print(colored('Immediate login not detected, ip"s chill','cyan'))
        return False

def check_for_pop_up(page):
    print("Checking for popup")
    pop_up_selectors = '.x1o1ewxj.x3x9cwd.x1e5q0jg.x13rtm0m.x78zum5.xdt5ytf.x1iyjqo2.x1al4vs7'
    hasPopup = page.query_selector(pop_up_selectors) is not None
    
    if hasPopup:
        print(colored('Popup exists.', 'red'))
        return True
    else:
        print(colored('Popup not present','green'))
        return False 
    
def email_listings(listings, query):
    subject = f"New Facebook Marketplace Listing(s)"
    body = generate_email_body(listings)
    if (len(body) == 0): return
    
    smtp_server = "smtp-mail.outlook.com"
    port = 587
    username = os.getenv('OUTLOOK_CLIENT_EMAIL')
    password = os.getenv('OUTLOOK_CLIENT_PASSWORD')
    to_email_main = "Thatfloridaman1234@gmail.com"
    to_email_cc = "na14de@gmail.com"

    # Create the email.
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email_main
    msg['Cc'] = to_email_cc
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    msg.add_header('X-Priority', '1')
    msg.add_header('Importance', 'High')
    msg.add_header('X-MSMail-Priority', 'High')

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(username, password)
    text = msg.as_string()
    cc_addresses = [to_email_cc]
    all_recipients = [msg['To']] + cc_addresses
    server.sendmail(username, all_recipients, text)
    server.quit()
    
    print(colored('Emailed listings!', 'green'))

def email_error_to_dev(error):
    smtp_server = "smtp-mail.outlook.com"
    port = 587  # For starttls
    username = os.getenv('OUTLOOK_CLIENT_EMAIL')
    password = os.getenv('OUTLOOK_CLIENT_PASSWORD')
    to_email = "nate.d.luna@gmail.com"
    body = "See error logs"
    # Create the email.
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = 'Error triggered: class name change'
    msg.attach(MIMEText(body, 'text'))

    # Send the email.
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(username, password)
    text = msg.as_string()
    server.sendmail(username, to_email, text)
    print(colored('Error email sent to dev.', 'red'))
    server.quit()
    print(colored('Email server closed.', 'red'))  
    
def generate_email_body(listings):
    body_html = ''
    for key,value in listings.items():
        pattern = r'\b(a minute ago|2 minutes ago|3 minutes ago|4 minutes ago|5 minutes ago|6 minutes ago|7 minutes ago|8 minutes ago|seconds ago)\b'
        if re.search(pattern, value["listed_time"]):
            print(colored('Listing found minutes ago!','green'))
            body_html += """
            <div style="margin-bottom: 100px;">
                <img src="{image_url}" style="width: 50%;">
                <h3>{price}</h3>
                <h4 style="font-weight: normal; color: green;">{listed_time}</h4>
                <a href="{post_url}" style="color: blue;">{title}</a>
                <br>
            </div>
            """.format(image_url=value["image_url"], price=value["price"], title=value["title"], location=value["location"], post_url=value["post_url"], listed_time=value["listed_time"])

    return body_html

def log_listing_count(count):
    file_name = 'listings_count_log.txt'

    with open(file_name, 'a') as file:
        file.write(f"{count}\n")
        
def check_recent_scrape_count():
    file_name = 'listings_count_log.txt'
    try:
        with open(file_name, 'r') as file:
            lines = file.readlines()

        if (len(lines) > 100):
            with open(file_name, 'w') as file:
                file.writelines(lines[50:])


        recent_numbers = [int(line.strip()) for line in lines[-10:]]
        print(colored(f'{recent_numbers}last 10 runs','cyan'))
        if all(number == 1 for number in recent_numbers):
            return True
        else:
            return False
    except FileNotFoundError:
        print("File not found. Please ensure the correct file path.")
        return False
    except ValueError:
        print("Error processing the file. Ensure it contains only numbers.")
        return False

def check_internet_connection():
    try:
        res = requests.get('https://www.google.com/', timeout=7)
        return {'status': True, 'code': res.status_code}
    except requests.ConnectionError as e:
        logging.error('Internet connection failed: %s', str(e))
        return {'status': False, 'error': str(e)}
    except requests.Timeout as e:
        logging.error('Internet connection timed out: %s', str(e))
        return {'status': False, 'error': 'Connection timed out'}

def parse_ip(env_var_value):
    ip_address, port, username, password = env_var_value.split(":")
    return {
        "ip_address": ip_address,
        "port": port,
        "username": username,
        "password": password
    }

async def main():
    c = check_internet_connection()
    if not c['status']:
        print(colored('No internet connection, check logger for details', 'red'))
        exit()
    print(colored('Internet connection established', 'green'))
    
    initial_url = "https://www.facebook.com/login/device-based/regular/login/"
    async with async_playwright() as p:
        parsed_ips = [parse_ip(os.getenv(f"RESIDENTIAL_IP{i}")) for i in range(1, 10) if os.getenv(f"RESIDENTIAL_IP{i}")]
        
        selected_ip = choice(parsed_ips)
        print(colored(f"Using {selected_ip["ip_address"]}", "cyan"))
        
        proxy_config = {
            'server': f'http://{selected_ip["ip_address"]}:{selected_ip["port"]}',
            'username': selected_ip["username"],
            'password': selected_ip["password"],
        }
        # # For residential royal proxys
        # proxy_config={
        #     'server': 'http://geo.iproyal.com:12321',
        #     'username': os.getenv('IPROYAL_USERNAME'),
        #     'password': os.getenv('IPROYAL_PASSWORD'),
        # }
        
        # proxy=proxy_config
        browser = await p.chromium.launch(headless=False, proxy=proxy_config)
            
        # browser = await p.chromium.launch(headless=False)
        
        print(colored('Opening a new browser page.', 'cyan'))
        context = await browser.new_context()
        page = await browser.new_page()
        time.sleep(2)
        for query_dict in QUERYS:
            print(colored('clearing cookies','cyan'))
            await context.clear_cookies()
            
            query = quote(query_dict["type"])
            city = quote(str(query_dict["city"]))
            scroll = query_dict["scroll"]
            expand_search_radius = query_dict["change_search_radius"]
            max_price = quote(str(query_dict["max_price"]))
            
            marketplace_url = f'https://www.facebook.com/marketplace/{city}/search/?query={query}&daysSinceListed=7&sortBy=creation_time_descend&minPrice=500&maxPrice={max_price}&exact=false'
            print(colored(f'Searching for{query} in {city}', 'cyan'))
            time.sleep(1)
            await page.goto(marketplace_url, wait_until='networkidle')
            await check_for_immediate_login_reroute(page, selected_ip["ip_address"])

            await check_for_login_popup(page)
            run = await scrape_through_listings(page, query, browser, scroll, expand_search_radius, p)

        await browser.close()
        
    

asyncio.run(main())

