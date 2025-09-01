import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime, timedelta

# Define search keywords
SEARCH_TERMS = ["acquisition India", "merger India", "M&A India"]

# Time window: last 90 days
cutoff_date = datetime.now() - timedelta(days=90)

# Helper: clean text
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

# Helper: try to extract buyer and target names from headline
def extract_companies(title):
    # Very naive rule: "X acquires Y" or "X buys Y"
    patterns = [
        r"(.+?) acquires (.+)",
        r"(.+?) buys (.+)",
        r"(.+?) acquires stake in (.+)",
        r"(.+?) merges with (.+)"
    ]
    for pat in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            return clean_text(m.group(1)), clean_text(m.group(2))
    return None, None

# Fetch articles from Google News RSS
def fetch_articles(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")
    
    results = []
    for item in items:
        title = item.title.text
        link = item.link.text
        pub_date = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
        
        if pub_date < cutoff_date:
            continue
        
        buyer, target = extract_companies(title)
        
        results.append({
            "date": pub_date.date(),
            "title": clean_text(title),
            "link": link,
            "buyer": buyer,
            "target": target
        })
    return results

# Collect from all search terms
all_results = []
for term in SEARCH_TERMS:
    all_results.extend(fetch_articles(term))

# Deduplicate by title
unique_results = {r["title"]: r for r in all_results}.values()

# Save to CSV
filename = f"india_mna_deals_{datetime.now().date()}.csv"
with open(filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "buyer", "target", "title", "link"])
    writer.writeheader()
    writer.writerows(unique_results)

print(f"✅ Saved {len(unique_results)} results to {filename}")
