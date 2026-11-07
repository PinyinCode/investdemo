import json
import os
import subprocess
import datetime
import requests

SYMBOLS_FILE = "vn100_symbols.json"

def get_vn100_symbols():
    print("🔄 Đang lấy danh sách mã VN100 trực tiếp từ API VCI...", flush=True)
    
    # API chính thức của VCI cho rổ VN100
    url = "https://trading.vietcap.com.vn/api/price/symbols/getList"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"group": "VN100"}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        
        # VCI trả về list các dict, key 'ticker' là mã
        symbols = [item["ticker"] for item in data if "ticker" in item]
        symbols = sorted(list(set(symbols))) # Loại trùng, sắp xếp
        
        if len(symbols) >= 100:
            with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
                json.dump(symbols, f, ensure_ascii=False, indent=4)
            print(f"✅ Đã lấy thành công {len(symbols)} mã VN100 và lưu vào {SYMBOLS_FILE}")
            return symbols
        else:
            print(f"⚠️ API VCI chỉ trả về {len(symbols)} mã. Có thể đang trong kỳ review.")
            # Vẫn lưu nếu bạn muốn, nhưng cảnh báo
            with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
                json.dump(symbols, f, ensure_ascii=False, indent=4)
            return symbols

    except Exception as e:
        print(f"❌ Lỗi khi gọi API VCI: {e}")
        
    return []

def auto_git_push_symbols():
    try:
        print(f"\n📤 Đang tự động đồng bộ file {SYMBOLS_FILE} lên GitHub...")
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        subprocess.run(["git", "pull", "origin", "main", "--rebase", "--autostash"], capture_output=True)
        
        subprocess.run(["git", "add", SYMBOLS_FILE], check=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("ℹ️ Không có dữ liệu danh sách nào thay đổi để đẩy lên.")
            return

        commit_msg = f"Auto update {SYMBOLS_FILE} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy danh sách lên GitHub thành công!")
        
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

if __name__ == "__main__":
    symbols = get_vn100_symbols()
    if symbols:
        auto_git_push_symbols()
