from playwright.sync_api import sync_playwright
import json, time, sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US"
    )

    # ===== PINTEREST =====
    print("=== Pinterest ===")
    page = context.new_page()
    page.goto("https://uk.pinterest.com/chictemplatebyamanda/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(8)

    for i in range(3):
        page.mouse.wheel(0, 800)
        time.sleep(2)

    boards = page.evaluate("""() => {
        const results = [];
        // Try various selectors for board cards
        const cards = document.querySelectorAll('[data-test-id="board"], [data-test-id="grid-item"], div[role="listitem"]');
        for (const card of cards) {
            const nameEl = card.querySelector('[data-test-id="board-name"], [title], h3, h2, span');
            const countEl = card.querySelector('[data-test-id="board-pin-count"], span');
            const name = nameEl ? nameEl.textContent.trim() : '';
            const count = countEl ? countEl.textContent.trim() : '';
            if (name && name.length > 2) {
                results.push({name, count});
            }
        }
        return results;
    }""")
    print(f"Boards from DOM: {len(boards)}")
    for b in boards:
        print(f"  {b['name']}: {b['count']}")

    # Also get all text content that looks like board info
    all_text = page.evaluate("""() => {
        const items = [];
        document.querySelectorAll('div[data-test-id], [role="listitem"]').forEach(el => {
            const text = el.textContent.trim();
            if (text.length > 3 && text.length < 200) {
                items.push(text);
            }
        });
        return items.slice(0, 30);
    }""")
    print(f"\nAll grid items: {len(all_text)}")
    for t in all_text:
        print(f"  {t[:100]}")

    page.close()

    # ===== TIKTOK =====
    print("\n=== TikTok ===")
    page2 = context.new_page()
    page2.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

    page2.goto("https://www.tiktok.com/@chictemplatebyamanda", wait_until="domcontentloaded", timeout=45000)
    time.sleep(10)

    # Get profile stats
    stats = page2.evaluate("""() => {
        const result = {};
        const followers = document.querySelector('[data-e2e="followers-count"]');
        const likes = document.querySelector('[data-e2e="likes-count"]');
        const following = document.querySelector('[data-e2e="following-count"]');
        result.followers = followers ? followers.textContent.trim() : 'N/A';
        result.likes = likes ? likes.textContent.trim() : 'N/A';
        result.following = following ? following.textContent.trim() : 'N/A';
        return result;
    }""")
    print(f"Profile stats: {json.dumps(stats)}")

    # Scroll to try to load videos
    for i in range(8):
        page2.mouse.wheel(0, 1000)
        time.sleep(2)

    # Get video thumbnails/captions from DOM
    videos = page2.evaluate("""() => {
        const results = [];
        // Try all anchor tags that might link to videos
        const links = document.querySelectorAll('a[href*="/video/"]');
        for (const link of links) {
            const href = link.href;
            const videoId = href.match(/video\\/(\\d+)/);
            if (videoId) {
                const caption = link.textContent.trim() || link.title || '';
                results.push({id: videoId[1], caption: caption.substring(0, 80), href: href});
            }
        }
        return results;
    }""")
    print(f"Video links: {len(videos)}")
    for v in videos[:10]:
        print(f"  Video {v['id']}: {v['caption'][:50]}")

    # Try getting video data from meta tags
    meta = page2.evaluate("""() => {
        const results = [];
        document.querySelectorAll('meta[property*="video"], meta[name*="video"]').forEach(m => {
            results.push({name: m.getAttribute('property') || m.getAttribute('name'), content: m.content});
        });
        return results;
    }""")
    print(f"\nVideo meta tags: {len(meta)}")
    for m in meta:
        print(f"  {m['name']}: {m['content'][:80]}")

    page2.close()
    browser.close()
