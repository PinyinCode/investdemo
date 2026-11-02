import os
import time
import datetime
import json
import subprocess
import requests

DATA_FILE = "data.json"

def update_realtime_prices():
    if not os.path.exists(DATA_FILE):
        print("❌ Không tìm thấy file data.json!")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    print(f"\n⚡ [Realtime] Bắt đầu quét giá mới cho {len(stock_db)} mã lúc {datetime.datetime.now().strftime('%H:%M:%S')}...")
    
    updated_count = 0
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for symbol, data in stock_db.items():
        if not isinstance(data, dict):
            continue
            
        try:
            # Gọi trực tiếp API công khai của TCBS lấy dữ liệu giá mới nhất
            url = f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/s-chart?ticker={symbol}&resolution=D&from=0&to=9999999999"
            r = requests.get(url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                json_data = r.json()
                if 'data' in json_data and json_data['data']:
                    latest = json_data['data'][-1]
                    new_close = float(latest.get('close', data.get('close', 0)))
                    new_volume = int(latest.get('volume', data.get('volume', 0)))
                    
                    if new_close > 0:
                        # Cập nhật trực tiếp vào data.json
                        data['close'] = new_close
                        data['volume'] = new_volume
                        data['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated_count += 1
        except Exception:
            pass
            
        time.sleep(0.1) # Nghỉ cực ngắn giữa các mã để quét siêu tốc

    # Ghi đè lại file data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Đã cập nhật xong giá thành công cho {updated_count}/{len(stock_db)} mã vào data.json.")
    
    # Tự động đẩy (push) lên GitHub Pages
    git_commit_and_push()

def git_commit_and_push():
    try:
        subprocess.run(["git", "add", DATA_FILE], check=True)
        commit_msg = f"Auto-update data.json prices at {datetime.datetime.now().strftime('%H:%M %d-%m-%Y')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đã tự động push data.json mới lên GitHub Pages!\n")
    except Exception as e:
        print(f"ℹ️ Không có thay đổi mới để push hoặc lỗi git: {e}\n")

def is_trading_time():
    """Kiểm tra giờ giao dịch chứng khoán (Thứ 2 - Thứ 6, từ 9:00 đến 15:00)"""
    now = datetime.datetime.now()
    if now.weekday() >= 5: # Cuối tuần
        return False
    current_time_val = now.hour * 60 + now.minute
    return (9 * 60) <= current_time_val <= (15 * 60)

if __name__ == "__main__":
    print("🤖 Hệ thống tự động cập nhật giá Realtime (chỉ data.json) đã khởi động!")
    
    while True:
        try:
            if is_trading_time():
                update_realtime_prices()
                print("💤 Đang trong giờ giao dịch. Chờ 30 phút để quét nhịp tiếp theo...")
                time.sleep(1800)
            else:
                print(f"🌙 Ngoài giờ giao dịch ({datetime.datetime.now().strftime('%H:%M %d-%m-%Y')}). Nghỉ 5 phút kiểm tra lại...")
                time.sleep(300)
        except Exception as e:
            print(f"⚠️ Lỗi vòng lặp: {e}")
            time.sleep(60)
