from datetime import datetime
import json
import subprocess
import sys
import urllib.request
import urllib.error
import traceback
import re

# ============================================================
# CONFIGURATION
# ============================================================
TIKTOK_USERNAME = "chictemplatebyamanda"
PINTEREST_USERNAME = "chictemplatebyamanda"
# ============================================================


def scrape_tiktok():
    """Scrape TikTok profile using yt-dlp (more reliable than headless browser)."""
    print(f"[TikTok] Fetching profile for @{TIKTOK_USERNAME}")
    try:
        url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}"
        result = subprocess.run(
            [
                sys.executable, "-m", "yt_dlp",
                "--flat-playlist",
                "--dump-json",
                "--playlist-items", "1:10",
                "--no-warnings",
                "--quiet",
                url
            ],
            capture_output=True, text=True, timeout=120
        )

        results = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                video = json.loads(line)
                title = video.get("title", video.get("description", "Untitled"))[:80]
                view_count = video.get("view_count")
                like_count = video.get("like_count")

                views = "N/A"
                if view_count is not None:
                    views = f"{view_count:,} views"
                elif like_count is not None:
                    views = f"{like_count:,} likes"

                results.append({"design": title, "views": views})
            except json.JSONDecodeError:
                continue

        print(f"[TikTok] Found {len(results)} videos")
        return results
    except subprocess.TimeoutExpired:
        print("[TikTok] Request timed out")
        return []
    except Exception as e:
        print(f"[TikTok] Failed: {e}")
        traceback.print_exc()
        return []


def scrape_pinterest():
    """Scrape Pinterest boards using their public data endpoint."""
    print(f"[Pinterest] Fetching boards for @{PINTEREST_USERNAME}")
    try:
        url = f"https://www.pinterest.com/{PINTEREST_USERNAME}/_saved/"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")

        # Extract board data from Pinterest's embedded JSON
        results = []

        # Look for board data in the page's initial data
        pattern = r'"name"\s*:\s*"([^"]+)".*?"pin_count"\s*:\s*(\d+)'
        matches = re.findall(pattern, html)

        if matches:
            for name, count in matches[:15]:
                results.append({"design": name, "views": f"{int(count)} pins"})

        # Fallback: try to extract from board grid items
        if not results:
            board_pattern = r'"board":\s*\{[^}]*"name"\s*:\s*"([^"]+)"'
            names = re.findall(board_pattern, html)
            for name in names[:15]:
                results.append({"design": name, "views": "pins"})

        print(f"[Pinterest] Found {len(results)} boards")
        return results
    except Exception as e:
        print(f"[Pinterest] Failed: {e}")
        traceback.print_exc()
        return []


def fetch_metrics():
    data = {
        "timestamp": datetime.now().strftime("%B %d, %Y - %H:%M:%S"),
        "tiktok": [],
        "pinterest": []
    }

    data["tiktok"] = scrape_tiktok()
    data["pinterest"] = scrape_pinterest()

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"[Done] Data written to data.json at {data['timestamp']}")


if __name__ == "__main__":
    fetch_metrics()
