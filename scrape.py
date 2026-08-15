from datetime import datetime
import json
import os

def fetch_metrics():
    # Structured data for your dashboard
    data = {
        "timestamp": datetime.now().strftime("%B %d, %Y - %H:%M:%S"),
        "tiktok": [
            {"design": "TikTok Video / Design 1", "views": "Updating..."},
            {"design": "TikTok Video / Design 2", "views": "Updating..."}
        ],
        "pinterest": [
            {"design": "Clipart Board", "views": "35 Pins (1h)"},
            {"design": "Emotional Wellness-Mindfulness", "views": "1 Pin (2mo)"},
            {"design": "Events/Parties/Invitations", "views": "2 Pins (2mo)"}
        ]
    }
    
    # Write to data.json which the webpage reads automatically
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    fetch_metrics()
