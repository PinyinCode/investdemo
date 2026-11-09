import os
import json
import base64
import requests
from pymongo import MongoClient

# LẤY THÔNG TIN TỪ SECRETS
MONGO_URI = os.environ.get("MONGO_URI", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()

if not all([MONGO_URI, GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO]):
    print("❌ LỖI: Thiếu biến môi trường (MONGO_URI, GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO)!")
    exit(1)

def get_history_from_github(symbol):
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/history/{symbol}.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            return json.loads(content)
    except Exception as e:
        print(f"⚠️ Lỗi tải history {symbol}: {e}")
    return None

def fix_prev_close():
    print("🔌 Đang kết nối MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client['quant_db']
    collection = db['stocks']

    all_symbols = [doc["symbol"] for doc in collection.find({}, {"symbol": 1})]
    print(f"🔍 Tìm thấy {len(all_symbols)} mã. Bắt đầu lấy giá chính xác từ History...\n")

    fixed_count = 0

    for sym in all_symbols:
        doc = collection.find_one({"symbol": sym})
        if not doc: continue

        close_price = doc.get("close", 0)
        prev_close = doc.get("prev_close", 0)

        # Nếu prev_close đang bị trùng với close (gây ra 0%), ta lấy từ history
        if close_price > 0 and prev_close == close_price:
            hist = get_history_from_github(sym)
            if hist and hist.get("history_d1"):
                bars = hist["history_d1"]
                
                if len(bars) >= 2:
                    # Lấy giá của nến áp chót (chính là phiên giao dịch trước đó)
                    exact_prev_close = bars[-2]["close"]
                    
                    # Chuẩn hóa đơn vị (nếu file history lưu 57.5 thay vì 57500)
                    if 0 < exact_prev_close < 1000:
                        exact_prev_close = exact_prev_close * 1000
                    
                    collection.update_one(
                        {"symbol": sym},
                        {"$set": {"prev_close": int(exact_prev_close)}}
                    )
                    fixed_count += 1
                    print(f"✅ {sym}: Sửa prev_close từ {prev_close:,} -> {exact_prev_close:,} (Lấy từ History {bars[-2]['time']})")
                else:
                    print(f"⚠️ {sym}: History không đủ 2 nến.")
            else:
                print(f"⚠️ {sym}: Không tìm thấy file history.")

    print(f"\n🎉 HOÀN TẤT! Đã sửa lỗi cho {fixed_count} mã.")

if __name__ == "__main__":
    fix_prev_close()
