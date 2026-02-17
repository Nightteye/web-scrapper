import time
import json
import re
import os
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TARGET_URL = "https://www.chordy.xyz/discord" # Change this to ANY site you want
MAX_SCROLLS = 5  # Limits how many times it scrolls down (to prevent infinite loops)
HEADLESS = False # Set to True to hide the browser
# ---------------------

def get_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    
    # Standard settings to look like a real user
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extract_all_data(driver, url):
    print(f"Scraping: {url}")
    driver.get(url)
    
    # 1. Smart Scrolling
    # We scroll a few times to trigger any lazy-loading images or content
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(MAX_SCROLLS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5) # Wait for content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    # 2. Parse HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 3. Data Containers
    page_data = {
        "metadata": {},
        "content": {
            "headings": [],
            "paragraphs": [],
            "tables": []
        },
        "links": [],
        "images": [],
        "emails": []
    }

    # --- EXTRACT METADATA ---
    if soup.title:
        page_data["metadata"]["title"] = soup.title.string.strip()
    
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        page_data["metadata"]["description"] = meta_desc.get("content", "").strip()

    # --- EXTRACT TEXT CONTENT ---
    # Get all headings (H1-H6)
    for i in range(1, 7):
        for h in soup.find_all(f'h{i}'):
            text = h.get_text(strip=True)
            if text:
                page_data["content"]["headings"].append({"level": f"h{i}", "text": text})
    
    # Get all paragraphs
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if len(text) > 20: # Filter out tiny snippets
            page_data["content"]["paragraphs"].append(text)

    # --- EXTRACT LINKS ---
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convert relative paths (/about) to full URLs (https://site.com/about)
        full_url = urljoin(url, href)
        text = link.get_text(strip=True)
        if text:
            page_data["links"].append({"text": text, "url": full_url})

    # --- EXTRACT IMAGES ---
    for img in soup.find_all('img', src=True):
        src = img['src']
        full_src = urljoin(url, src)
        alt = img.get('alt', '')
        page_data["images"].append({"src": full_src, "alt_text": alt})

    # --- EXTRACT EMAILS (REGEX) ---
    # This scans the entire text of the page for email patterns
    page_text = soup.get_text()
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text))
    page_data["emails"] = list(emails)

    return page_data

def save_data(data, url):
    # Create a filename based on the domain
    domain = urlparse(url).netloc.replace("www.", "")
    filename = f"{domain}_data.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"\n--- SUCCESS ---")
    print(f"Data saved to: {filename}")
    print(f"Found {len(data['content']['headings'])} headings")
    print(f"Found {len(data['content']['paragraphs'])} paragraphs")
    print(f"Found {len(data['links'])} links")
    print(f"Found {len(data['images'])} images")
    print(f"Found {len(data['emails'])} emails")

if __name__ == "__main__":
    driver = None
    try:
        driver = get_driver()
        data = extract_all_data(driver, TARGET_URL)
        save_data(data, TARGET_URL)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()