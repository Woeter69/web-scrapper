import os
import json
import requests
import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def get_config():
    """Retrieves configuration from environment variables."""
    return {
        "user_agent": os.getenv("USER_AGENT", "GlobalWebScraper/1.0"),
        "mongo_uri": os.getenv("MONGODB_URI"),
        "db_name": os.getenv("MONGODB_DB_NAME", "web_scraper"),
        "collection": os.getenv("MONGODB_COLLECTION", "scraped_pages"),
        "max_pages": int(os.getenv("MAX_PAGES_PER_SITE", 10)),
        "delay": int(os.getenv("CRAWL_DELAY", 1))
    }

def get_db_collection():
    """Returns a MongoDB collection object if URI is provided."""
    config = get_config()
    if not config["mongo_uri"]:
        return None
    try:
        client = MongoClient(config["mongo_uri"], serverSelectionTimeoutMS=2000)
        # Test connection
        client.server_info()
        db = client[config["db_name"]]
        return db[config["collection"]]
    except Exception as e:
        print(f"⚠️ MongoDB Connection failed: {e}. Falling back to JSON only.")
        return None

def check_robots_txt(url, user_agent):
    """Checks robots.txt permissions."""
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    rp = RobotFileParser()
    try:
        rp.set_url(f"{base_url}/robots.txt")
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return True

def extract_content(html, url):
    """Parses HTML and extracts structured data."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()

    # Basic metadata
    data = {
        'url': url,
        'domain': urlparse(url).netloc,
        'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
        'title': soup.title.string.strip() if soup.title else "No Title",
        'headings': [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])],
        'paragraphs': [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20],
        'links': []
    }

    # Extract internal links for crawling
    base_domain = urlparse(url).netloc
    for a in soup.find_all('a', href=True):
        link = urljoin(url, a['href'])
        parsed_link = urlparse(link)
        # Only collect links from the same domain
        if parsed_link.netloc == base_domain:
            data['links'].append(link)
    
    data['links'] = list(set(data['links'])) # De-duplicate
    return data

def save_data(data, collection=None):
    """Saves data to MongoDB or local JSON file."""
    # 1. Save to MongoDB if available
    if collection is not None:
        try:
            collection.update_one({'url': data['url']}, {'$set': data}, upsert=True)
            print(f"  [DB] Synced {data['url']}")
        except Exception as e:
            print(f"  [DB] Error: {e}")

    # 2. Always save a local copy as JSON
    domain_folder = f"scrapped-data/{data['domain']}"
    os.makedirs(domain_folder, exist_ok=True)
    
    # Sanitize filename (URL to filename)
    filename = data['url'].replace('https://', '').replace('http://', '').replace('/', '_').replace('?', '_')[:100] + ".json"
    filepath = os.path.join(domain_folder, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def crawl_site(start_url):
    """Recursively crawls a site starting from a URL."""
    config = get_config()
    db_col = get_db_collection()
    
    to_visit = [start_url]
    visited = set()
    pages_scraped = 0

    print(f"\n🚀 Starting Global Scrape on: {start_url}")
    print(f"Max Pages: {config['max_pages']} | Robots.txt: Active")

    while to_visit and pages_scraped < config['max_pages']:
        current_url = to_visit.pop(0)
        
        if current_url in visited:
            continue
        
        # Respect robots.txt
        if not check_robots_txt(current_url, config['user_agent']):
            print(f"🚫 Skipped (Robots.txt): {current_url}")
            continue

        try:
            print(f"🔎 Scraping ({pages_scraped+1}/{config['max_pages']}): {current_url}")
            response = requests.get(current_url, headers={'User-Agent': config['user_agent']}, timeout=10)
            response.raise_for_status()
            
            # Extract
            page_data = extract_content(response.text, current_url)
            
            # Save
            save_data(page_data, db_col)
            
            # Add new links to queue
            visited.add(current_url)
            pages_scraped += 1
            
            for link in page_data['links']:
                if link not in visited:
                    to_visit.append(link)

            # Polite delay
            time.sleep(config['delay'])

        except Exception as e:
            print(f"❌ Failed to scrape {current_url}: {e}")
            visited.add(current_url)

    print(f"\n✅ Finished! Scraped {pages_scraped} pages.")

def main():
    print("--- Global Multi-Page Web Scraper ---")
    url = input("Enter starting URL: ").strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    crawl_site(url)

if __name__ == "__main__":
    main()
