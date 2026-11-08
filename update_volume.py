import os
import json
import base64
import requests
from pymongo import MongoClient

# ===================== CONFIG =====================
MONGO_URI = os.environ.get("MONGO_URI", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()

def get_history_from_github(symbol):
    if not all([GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO]): return None
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/history/{symbol}.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            return json.loads(content)
    except Exception:
        pass
    return None

def update_volume_percent():
    print("🔌 Đang kết nối MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client['quant_db']
    collection = db['stocks']

    all_symbols = [doc["symbol"] for doc in collection.find({}, {"symbol": 1})]
    print(f"🔍 Tìm thấy {len(all_symbols)} mã. Bắt đầu tính KL đột biến...\n")

    updated_count = 0

    for sym in all_symbols:
        doc = collection.find_one({"symbol": sym})
        if not doc: continue

        current_volume = doc.get("volume", 0)
        current_open = doc.get("open", 0)
        current_high = doc.get("high", 0)
        current_low = doc.get("low", 0)
        
        # Tính biên độ (Amplitude)
        amplitude_percent = 0.0
        if current_open > 0 and current_high > 0 and current_low > 0:
            raw_amp = (current_high - current_low) / current_open * 100
            if 0 <= raw_amp <= 30.0:
                amplitude_percent = round(raw_amp, 2)

        # Lấy dữ liệu lịch sử để tính KL trung bình 20 phiên
        hist = get_history_from_github(sym)
        volume_percent = 0.0
        if hist and hist.get("history_d1"):
            bars = hist["history_d1"]
            recent_volumes = [b.get("volume", 0) for b in bars[-20:]]
            if recent_volumes:
                avg_volume_20 = sum(recent_volumes) / len(recent_volumes)
                if avg_volume_20 > 0 and current_volume > 0:
                    raw_vol = current_volume / avg_volume_20 * 100
                    if 0 <= raw_vol <= 1000.0:
                        volume_percent = round(raw_vol, 2)

        # Cập nhật vào DB
        if amplitude_percent > 0 or volume_percent > 0:
            collection.update_one(
                {"symbol": sym},
                {"$set": {
                    "amplitude_percent": amplitude_percent,
                    "volume_percent": volume_percent
                }}
            )
            updated_count += 1
            print(f"✅ {sym}: Biên độ {amplitude_percent}% | Vol {volume_percent}%")

    print(f"\n🎉 HOÀN TẤT! Đã cập nhật KL đột biến cho {updated_count} mã.")

if __name__ == "__main__":
    update_volume_percent()
