import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime, timedelta
import pandas as pd

SEARCH_TERMS = ["acquisition India", "merger India", "M&A India"]
cutoff_date = datetime.now() - timedelta(days=90)

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_companies(title):
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

def main():
    st.title("📊 Recent Acquisitions in India")
    st.write("Fetching acquisition/merger news from the past 3 months...")

    all_results = []
    for term in SEARCH_TERMS:
        all_results.extend(fetch_articles(term))

    unique_results = {r["title"]: r for r in all_results}.values()
    df = pd.DataFrame(unique_results)

    if not df.empty:
        st.success(f"Found {len(df)} results")
        st.dataframe(df)

        # Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name=f"india_mna_{datetime.now().date()}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No recent acquisitions found.")

if __name__ == "__main__":
    main()
