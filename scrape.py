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
        time.sleep(random.uniform(6, 10))

        # Get profile stats
        stats = page.evaluate("""() => {
            const followers = document.querySelector('[data-e2e="followers-count"]');
            const likes = document.querySelector('[data-e2e="likes-count"]');
            const following = document.querySelector('[data-e2e="following-count"]');
            return {
                followers: followers ? followers.textContent.trim() : null,
                likes: likes ? likes.textContent.trim() : null,
                following: following ? following.textContent.trim() : null,
            };
        }""")

        # Try to get video list from UNIVERSAL_DATA
        universal = page.evaluate("""() => {
            const el = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
            if (!el) return null;
            const data = JSON.parse(el.textContent);
            const scope = data['__DEFAULT_SCOPE__'] || {};
            const userDetail = scope['webapp.user-detail'] || {};
            const userInfo = userDetail.userInfo || {};
            const user = userInfo.user || {};
            const userStats = userInfo.stats || {};
            const post = scope['webapp.user-post'] || {};
            return {
                nickname: user.nickname || null,
                videoCount: userStats.videoCount || null,
                followerCount: userStats.followerCount || null,
                heartCount: userStats.heartCount || null,
                itemList: (post.itemList || []).map(item => ({
                    desc: (item.desc || '').substring(0, 80),
                    views: (item.stats || {}).playCount || 0,
                    likes: (item.stats || {}).diggCount || 0,
                })),
            };
        }""")

        results = []

        if universal and universal.get("itemList"):
            for item in universal["itemList"]:
                views = item.get("views", 0)
                results.append({
                    "design": item.get("desc", "Untitled") or "Untitled",
                    "views": f"{views:,} views" if views else "N/A"
                })
            print(f"[TikTok] Got {len(results)} videos from UNIVERSAL_DATA")
        else:
            # Fallback: try scrolling and DOM extraction
            for i in range(5):
                page.mouse.wheel(0, 1000)
                time.sleep(random.uniform(1, 3))

            video_links = page.evaluate("""() => {
                const results = [];
                const links = document.querySelectorAll('a[href*="/video/"]');
                const seen = new Set();
                for (const link of links) {
                    const match = link.href.match(/video\\/(\\d+)/);
                    if (match && !seen.has(match[1])) {
                        seen.add(match[1]);
                        results.push({
                            id: match[1],
                            caption: (link.title || link.textContent.trim() || 'Untitled').substring(0, 80),
                        });
                    }
                }
                return results;
            }""")

            if video_links:
                for v in video_links[:10]:
                    results.append({"design": v["caption"], "views": "Video"})
                print(f"[TikTok] Got {len(results)} videos from DOM links")
            else:
                print("[TikTok] Video list not available (anti-bot blocking)")

        # Add profile summary as first entry if we have stats
        if universal and universal.get("nickname"):
            follower_count = universal.get("followerCount") or (stats.get("followers") if stats else None)
            heart_count = universal.get("heartCount") or (stats.get("likes") if stats else None)
            video_count = universal.get("videoCount")
            summary = f"Profile: {follower_count or 'N/A'} followers, {heart_count or 'N/A'} likes"
            if video_count:
                summary += f", {video_count} videos"
            results.insert(0, {"design": summary, "views": ""})

        print(f"[TikTok] Total entries: {len(results)}")
        return results

    except Exception as e:
        print(f"[TikTok] Scraping failed: {e}")
        traceback.print_exc()
        return []


def scrape_pinterest(page):
    """Scrape Pinterest boards for names and pin counts."""
    print(f"[Pinterest] Navigating to {PINTEREST_URL}")
    try:
        page.goto(PINTEREST_URL, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(5, 8))

        # Scroll to load all boards
        for i in range(3):
            page.mouse.wheel(0, 800)
            time.sleep(random.uniform(1, 3))

        boards = page.evaluate("""() => {
            const results = [];
            const seen = new Set();
            const items = document.querySelectorAll('div[data-test-id="grid-item"], [role="listitem"]');
            for (const item of items) {
                const text = item.textContent.trim();
                // Match pattern like "BoardName, XX Pins·, Xh/Xmo"
                const match = text.match(/^(.+?),\\s*(\\d+)\\s*Pin/);
                if (match) {
                    const name = match[1].trim();
                    const count = match[2];
                    if (!seen.has(name) && name.length > 2) {
                        seen.add(name);
                        results.push({name, count: count + ' Pins'});
                    }
                }
            }
            return results;
        }""")

        results = []
        for board in boards:
            results.append({"design": board["name"], "views": board["count"]})

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

    print(f"\n[Done] Data written to data.json at {data['timestamp']}")


if __name__ == "__main__":
    fetch_metrics()
