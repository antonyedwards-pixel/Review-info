from datetime import datetime
import json
import time
import random

# ============================================================
# CONFIGURATION - Update these URLs with your profile pages
# ============================================================
TIKTOK_PROFILE = "https://www.tiktok.com/@chictemplatebyamanda"
PINTEREST_PROFILE = "https://uk.pinterest.com/chictemplatebyamanda/"
# ============================================================


def scrape_tiktok(page):
    """Scrape TikTok profile for video metrics."""
    print(f"[TikTok] Navigating to {TIKTOK_PROFILE}")
    try:
        page.goto(TIKTOK_PROFILE, wait_until="networkidle", timeout=30000)
        time.sleep(random.uniform(3, 6))

        videos = page.query_selector_all('[data-e2e="user-post-item"]')
        if not videos:
            videos = page.query_selector_all('div[class*="DivVideoFeedV2"] > div > div')

        results = []
        for video in videos[:10]:
            try:
                title_el = video.query_selector('a[title]')
                title = title_el.get_attribute("title") if title_el else "Untitled"

                views_el = video.query_selector('strong[data-e2e="video-views"]')
                if not views_el:
                    views_el = video.query_selector('strong')
                views = views_el.inner_text() if views_el else "N/A"

                results.append({"design": title, "views": views})
            except Exception as e:
                print(f"[TikTok] Error parsing video: {e}")
                continue

        print(f"[TikTok] Found {len(results)} videos")
        return results
    except Exception as e:
        print(f"[TikTok] Scraping failed: {e}")
        return []


def scrape_pinterest(page):
    """Scrape Pinterest profile for board metrics."""
    print(f"[Pinterest] Navigating to {PINTEREST_PROFILE}")
    try:
        page.goto(PINTEREST_PROFILE, wait_until="networkidle", timeout=30000)
        time.sleep(random.uniform(3, 6))

        boards = page.query_selector_all('[data-test-id="board"]')
        if not boards:
            boards = page.query_selector_all('div[data-test-id="grid-item"]')

        results = []
        for board in boards[:15]:
            try:
                title_el = board.query_selector('[data-test-id="board-name"]')
                if not title_el:
                    title_el = board.query_selector('span')
                title = title_el.inner_text() if title_el else "Untitled"

                count_el = board.query_selector('[data-test-id="board-pin-count"]')
                if not count_el:
                    count_el = board.query_selector('div[class*="pinCount"]')
                count = count_el.inner_text() if count_el else "N/A"

                results.append({"design": title, "views": count})
            except Exception as e:
                print(f"[Pinterest] Error parsing board: {e}")
                continue

        print(f"[Pinterest] Found {len(results)} boards")
        return results
    except Exception as e:
        print(f"[Pinterest] Scraping failed: {e}")
        return []


def fetch_metrics():
    from playwright.sync_api import sync_playwright

    data = {
        "timestamp": datetime.now().strftime("%B %d, %Y - %H:%M:%S"),
        "tiktok": [],
        "pinterest": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = context.new_page()

        data["tiktok"] = scrape_tiktok(page)
        data["pinterest"] = scrape_pinterest(page)

        browser.close()

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"[Done] Data written to data.json at {data['timestamp']}")


if __name__ == "__main__":
    fetch_metrics()
