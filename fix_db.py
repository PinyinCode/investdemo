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

if not MONGO_URI:
    print("❌ LỖI: Thiếu MONGO_URI!")
    exit(1)

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

def fix_database():
    print("🔌 Đang kết nối MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client['quant_db']
    collection = db['stocks']

    all_symbols = [doc["symbol"] for doc in collection.find({}, {"symbol": 1})]
    print(f"🔍 Tìm thấy {len(all_symbols)} mã. Bắt đầu quét và làm sạch dữ liệu...\n")

    fixed_count = 0

    for sym in all_symbols:
        doc = collection.find_one({"symbol": sym})
        if not doc: continue

        prev_close = doc.get("prev_close", 0)
        trading_date = doc.get("trading_date", "")
        updated = False
        new_prev_close = prev_close

        # 1. Nếu prev_close đang bị lỗi đơn vị nghìn đồng (VD: 57.5)
        if 0 < prev_close < 1000:
            new_prev_close = prev_close * 1000
            updated = True
            print(f"🔧 {sym}: Sửa lỗi đơn vị {prev_close} -> {new_prev_close}")

        # 2. Nếu prev_close đang bị bằng 0 (chưa có) -> Lấy từ Github history
        elif prev_close == 0:
            hist = get_history_from_github(sym)
            if hist and hist.get("history_d1"):
                bars = hist["history_d1"]
                if len(bars) >= 1:
                    last_bar = bars[-1]
                    if last_bar["time"] == trading_date and len(bars) >= 2:
                        new_prev_close = bars[-2]["close"]
                    else:
                        new_prev_close = last_bar["close"]

                    if 0 < new_prev_close < 1000:
                        new_prev_close = new_prev_close * 1000
                    
                    updated = True
                    print(f"🔄 {sym}: Lấy từ history -> {new_prev_close}")

        # 3. Lưu lại vào DB nếu có thay đổi
        if updated and new_prev_close > 0:
            collection.update_one(
                {"symbol": sym},
                {"$set": {"prev_close": new_prev_close}}
            )
            fixed_count += 1

    print(f"\n✅ HOÀN TẤT! Đã sửa dữ liệu cho {fixed_count} mã.")
    print("👉 Bây giờ bạn ra web, bấm Ctrl + F5 để xem kết quả.")

if __name__ == "__main__":
    fix_database()
