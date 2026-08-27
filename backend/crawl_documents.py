import requests

from crawler import crawl, SEED_URL, MAX_PAGES, MAX_DEPTH

API_URL = "http://127.0.0.1:8000/documents/crawl"

def crawl_and_ingest():
    pages = crawl(SEED_URL, MAX_PAGES, MAX_DEPTH)

    for page in pages:
        response = requests.post(API_URL, json={
            "title": page["title"],
            "url": page["canonical_url"],
            "content": page["text"]
        })
        response.raise_for_status()

if __name__ == "__main__":
    crawl_and_ingest()
