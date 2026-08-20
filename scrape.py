from datetime import datetime
import json
import time
import random
import traceback

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
        page.goto(TIKTOK_PROFILE, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(5, 10))

        # Scroll to load content
        for _ in range(3):
            page.mouse.wheel(0, 800)
            time.sleep(random.uniform(1, 3))

        results = []

        # Try multiple selector strategies
        videos = page.query_selector_all('[data-e2e="user-post-item"]')
        if not videos:
            videos = page.query_selector_all('div[class*="DivVideoFeed"] div[class*="DivItemContainer"]')
        if not videos:
            videos = page.query_selector_all('div[data-e2e="user-post-item-list"] > div')

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
        traceback.print_exc()
        return []


def scrape_pinterest(page):
    """Scrape Pinterest profile for board metrics."""
    print(f"[Pinterest] Navigating to {PINTEREST_PROFILE}")
    try:
        page.goto(PINTEREST_PROFILE, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(5, 10))

        # Scroll to load content
        for _ in range(3):
            page.mouse.wheel(0, 800)
            time.sleep(random.uniform(1, 3))

        results = []

        # Try multiple selector strategies
        boards = page.query_selector_all('[data-test-id="board"]')
        if not boards:
            boards = page.query_selector_all('div[data-test-id="grid-item"]')
        if not boards:
            boards = page.query_selector_all('div[class*="board"]')

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
        traceback.print_exc()
        return []


def fetch_metrics():
    from playwright.sync_api import sync_playwright

    data = {
        "timestamp": datetime.now().strftime("%B %d, %Y - %H:%M:%S"),
        "tiktok": [],
        "pinterest": []
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            page = context.new_page()

            # Mask automation detection
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)

            data["tiktok"] = scrape_tiktok(page)
            data["pinterest"] = scrape_pinterest(page)

            browser.close()
    except Exception as e:
        print(f"[Fatal] Browser error: {e}")
        traceback.print_exc()

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"[Done] Data written to data.json at {data['timestamp']}")


if __name__ == "__main__":
    fetch_metrics()
