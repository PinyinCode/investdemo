import os
import datetime
import time
import json
import subprocess
import requests

DATA_FILE = "data.json"

VN100_SYMBOLS = [
    "ACB", "BID", "CTG", "TCB", "MBB", "STB", "VPB", "HDB", "VIB", "TPB",
    "SHB", "SSB", "LPB", "MSB", "OCB", "EIB", "SSI", "VCI", "HCM", "VIX",
    "MBS", "FTS", "BSI", "CTS", "ORS", "VHM", "VIC", "VRE", "NVL", "PDR",
    "DIG", "NLG", "KDH", "CEO", "DXG", "TCH", "HDG", "KBC", "IDC", "SZC",
    "BCM", "PHR", "HPG", "HSG", "NKG", "CTD", "VCG", "HHV", "FPT", "MWG",
    "PNJ", "FRT", "VNM", "MSN", "SAB", "GAS", "PVD", "PVS", "BSR", "POW",
    "REE", "PC1", "NT2", "GMD", "HAH", "PVT", "VJC", "HVN", "VHC", "ANV"
]

def auto_git_push():
    """Tự động đồng bộ file data.json lên GitHub"""
    try:
        print("📤 Đang tiến hành đồng bộ data.json lên GitHub...")
        subprocess.run(["git", "add", DATA_FILE], check=True)
            
        commit_msg = f"Auto-update realtime price lite - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Đẩy dữ liệu lên GitHub thành công!")
    except subprocess.CalledProcessError:
        print("⚠️ Git: Không có thay đổi giá mới để push.")
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

def main():
    print("⚡ Bắt đầu quét nhanh giá real-time (Lite) cho VN100...")

    stock_db = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                stock_db = json.load(f)
        except Exception:
            pass

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    updated_count = 0

    for i, symbol in enumerate(VN100_SYMBOLS):
        try:
            # Sử dụng API s-chart của TCBS để lấy thông tin nến mới nhất cực nhanh
            url = f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/s-chart?ticker={symbol}&resolution=D&from=0&to=9999999999"
            r = requests.get(url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                json_data = r.json()
                if 'data' in json_data and json_data['data']:
                    latest = json_data['data'][-1]
                    close_price = float(latest.get('close', 0))
                    volume = int(latest.get('volume', 0))

                    if close_price > 0:
                        # Nếu mã đã tồn tại trong data.json, tiến hành cập nhật đè giá & volume mới
                        if symbol in stock_db:
                            stock_db[symbol]["close"] = int(close_price * 1000)
                            stock_db[symbol]["volume"] = volume
                            stock_db[symbol]["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            # Nếu chưa có, khởi tạo cấu trúc tối thiểu
                            stock_db[symbol] = {
                                "symbol": symbol,
                                "close": int(close_price * 1000),
                                "volume": volume,
                                "pe": 0, "pb": 0, "eps": 0, "roe": 0, "roa": 0, "dividend_yield": 0,
                                "recommendation": "ĐANG TÍCH LŨY NỀN",
                                "price_zone": "",
                                "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "bctc_history": []
                            }
                        updated_count += 1
        except Exception as e:
            print(f"⚠️ Lỗi quét giá nhanh mã {symbol}: {e}")
        
        time.sleep(0.1) # Nghỉ ngắn giữa các request để siêu tốc và an toàn

    # Lưu lại file data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Đã cập nhật giá thành công cho {updated_count}/{len(VN100_SYMBOLS)} mã vào {DATA_FILE}!")

    auto_git_push()

if __name__ == "__main__":
    main()
