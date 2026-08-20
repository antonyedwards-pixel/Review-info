from datetime import datetime
import json
import time
import random
import traceback

# ============================================================
# CONFIGURATION
# ============================================================
TIKTOK_USERNAME = "chictemplatebyamanda"
PINTEREST_URL = "https://uk.pinterest.com/chictemplatebyamanda/"
# ============================================================


def scrape_tiktok(page):
    """Scrape TikTok profile for stats and video data."""
    print(f"[TikTok] Navigating to @{TIKTOK_USERNAME}")
    try:
        page.goto(f"https://www.tiktok.com/@{TIKTOK_USERNAME}", wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(8, 12))

        data = page.evaluate("""() => {
            const el = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
            if (!el) return null;
            const d = JSON.parse(el.textContent);
            const scope = d['__DEFAULT_SCOPE__'] || {};
            const ud = (scope['webapp.user-detail'] || {}).userInfo || {};
            const user = ud.user || {};
            const stats = ud.stats || {};
            const post = scope['webapp.user-post'] || {};
            return {
                nickname: user.nickname || null,
                description: user.signature || null,
                followerCount: stats.followerCount || 0,
                heartCount: stats.heartCount || 0,
                videoCount: stats.videoCount || 0,
                itemList: (post.itemList || []).map(item => ({
                    desc: (item.desc || '').substring(0, 80),
                    views: (item.stats || {}).playCount || 0,
                    likes: (item.stats || {}).diggCount || 0,
                })),
            };
        }""")

        if not data:
            print("[TikTok] No data found")
            return []

        results = []

        # If we got video items with view counts
        if data.get("itemList"):
            for item in data["itemList"]:
                views = item.get("views", 0)
                label = f"{views:,} views" if views else "N/A"
                results.append({"design": item.get("desc", "Untitled") or "Untitled", "views": label})
            print(f"[TikTok] Got {len(results)} videos with view counts")
        else:
            # Profile summary
            results.append({
                "design": f"{data['nickname']}: {data['videoCount']} videos",
                "views": f"{data['followerCount']:,} followers / {data['heartCount']:,} likes"
            })

        print(f"[TikTok] Total: {len(results)} entries")
        return results

    except Exception as e:
        print(f"[TikTok] Failed: {e}")
        traceback.print_exc()
        return []


def scrape_pinterest(page):
    """Scrape Pinterest boards with pin counts."""
    print(f"[Pinterest] Navigating to {PINTEREST_URL}")
    try:
        page.goto(PINTEREST_URL, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(6, 10))

        for i in range(3):
            page.mouse.wheel(0, 800)
            time.sleep(random.uniform(1, 2))

        boards = page.evaluate("""() => {
            const results = [];
            const seen = new Set();
            const items = document.querySelectorAll('div[data-test-id="grid-item"], [role="listitem"]');
            for (const item of items) {
                const text = item.textContent.trim();
                const match = text.match(/^(.+?),\\s*(\\d+)\\s*Pin/);
                if (match) {
                    const name = match[1].trim();
                    const count = match[2];
                    if (!seen.has(name) && name.length > 2) {
                        seen.add(name);
                        results.push({name: name, count: parseInt(count)});
                    }
                }
            }
            return results;
        }""")

        results = []
        total_pins = 0
        for board in boards:
            count = board["count"]
            total_pins += count
            results.append({"design": board["name"], "views": f"{count} Pins"})

        # Add summary
        if results:
            results.insert(0, {
                "design": f"Total: {len(boards)} boards",
                "views": f"{total_pins} Pins"
            })

        print(f"[Pinterest] Found {len(boards)} boards, {total_pins} total pins")
        return results

    except Exception as e:
        print(f"[Pinterest] Failed: {e}")
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
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            data["tiktok"] = scrape_tiktok(page)
            data["pinterest"] = scrape_pinterest(page)

            browser.close()
    except Exception as e:
        print(f"[Fatal] Browser error: {e}")
        traceback.print_exc()

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"\n[Done] Written to data.json at {data['timestamp']}")


if __name__ == "__main__":
    fetch_metrics()
