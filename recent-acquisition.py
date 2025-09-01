import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pandas as pd
import io

# Business-focused queries
SEARCH_TERMS = [
    "company acquisition India",
    "corporate acquisition India",
    "startup acquisition India",
    "merger and acquisition India",
    "business acquisition India"
]

# Time window: last 90 days
cutoff_date = datetime.now() - timedelta(days=90)

# Keyword filters
EXCLUDE_KEYWORDS = [
    "land acquisition", "government", "railway", "submarine", "army",
    "navy", "missile", "defence", "defense", "property", "road"
]

INCLUDE_KEYWORDS = [
    "company", "startup", "merger", "acquires", "buys", "stake", "deal", "subsidiary", "investment"
]

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

def is_relevant(title):
    title_lower = title.lower()
    if any(word in title_lower for word in EXCLUDE_KEYWORDS):
        return False
    if any(word in title_lower for word in INCLUDE_KEYWORDS):
        return True
    return False

def fetch_articles(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")
    
    results = []
    for item in items:
        title = item.title.text
        if not is_relevant(title):
            continue
        
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
    st.write("Fetching acquisition/merger news from the past 3 months (business-focused only).")

    all_results = []
    for term in SEARCH_TERMS:
        all_results.extend(fetch_articles(term))

    unique_results = {r["title"]: r for r in all_results}.values()
    df = pd.DataFrame(unique_results)

    if not df.empty:
        st.success(f"Found {len(df)} relevant results")
        st.dataframe(df)

        # --- Export to Excel with hyperlinks ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Deals", index=False)
            workbook  = writer.book
            worksheet = writer.sheets["Deals"]

            # Find column indexes
            title_col = df.columns.get_loc("title")
            link_col = df.columns.get_loc("link")

            # Replace title with hyperlink
            for row in range(len(df)):
                url = df.iloc[row, link_col]
                text = df.iloc[row, title_col]
                worksheet.write_url(row + 1, title_col, url, string=text)

        st.download_button(
            label="📥 Download Excel with Hyperlinks",
            data=output.getvalue(),
            file_name=f"india_mna_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No relevant acquisitions found.")

if __name__ == "__main__":
    main()
