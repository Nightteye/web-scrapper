import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# If Selenium can't find Chrome, uncomment the line below that matches your OS
# and make sure the path points to your actual chrome.exe file.

# WINDOWS Default Locations (Try these):
# CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
# CHROME_PATH = os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")



# Set this to None if you want to try auto-detection again
CHROME_PATH = None
# ---------------------

def scrape_infinite_scroll():
    print("Initializing the browser...")
    
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # Manually set the binary location if specified above
    if CHROME_PATH:
        if os.path.exists(CHROME_PATH):
            print(f"Using Custom Chrome Path: {CHROME_PATH}")
            options.binary_location = CHROME_PATH
        else:
            print(f"ERROR: Could not find Chrome at {CHROME_PATH}")
            print("Please check the path in the script configuration.")
            return

    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print("\nCRITICAL ERROR: Selenium still cannot open Chrome.")
        print(f"Error details: {e}")
        return

    # 2. Go to the target website
    url = "http://quotes.toscrape.com/scroll"
    print(f"Navigating to {url}")
    driver.get(url)

    # 3. Handle Infinite Scroll
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        print("Scrolling down...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached the bottom of the page!")
            break
        last_height = new_height

    # 4. Extract Data
    print("Parsing data...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    quotes_data = []
    quotes = soup.find_all('div', class_='quote')

    for quote in quotes:
        text = quote.find('span', class_='text').text
        author = quote.find('small', class_='author').text
        quotes_data.append({'author': author, 'quote': text})

    driver.quit()
    save_to_csv(quotes_data)

def save_to_csv(data):
    filename = 'infinite_quotes.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'quote'])
        writer.writeheader()
        writer.writerows(data)
    print(f"Success! Saved {len(data)} quotes to '{filename}'")

if __name__ == "__main__":
    scrape_infinite_scroll()