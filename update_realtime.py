import json
import os
import time
import concurrent.futures
from datetime import datetime
from lotusmarket import fetchers

DATA_FILE = "data.json"
SYMBOLS_FILE = "vn100_symbols.json"
LAST_UPDATE_FILE = "last_update.json"

def get_symbols():
    """Đọc danh sách mã từ file JSON"""
    if os.path.exists(SYMBOLS_FILE):
        try:
            with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], dict):
                        return [item["symbol"] for item in data if "symbol" in item]
                    return data
        except Exception as e:
            print(f"⚠️ Lỗi đọc {SYMBOLS_FILE}: {e}", flush=True)
    
    # Fallback: Nếu không có file symbols, đọc key từ data.json
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return list(json.load(f).keys())
        except Exception:
            pass
            
    print(f"❌ Không tìm thấy {SYMBOLS_FILE} hoặc {DATA_FILE}.", flush=True)
    return []

def fetch_price_with_timeout(symbol, timeout=8):
    """Lấy giá từ lotusmarket với timeout để tránh bị treo trên Github Actions"""
    def fetch():
        try:
            stock = fetchers.vps(symbol)
            return getattr(stock, "close", 0)
        except Exception:
            return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fetch)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return 0
        except Exception:
            return 0

def main():
    symbols = get_symbols()
    if not symbols:
        return

    # Đọc data.json hiện tại để giữ lại các thông tin cũ (tên cty, SLCP, v.v.)
    stock_db = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                stock_db = json.load(f)
        except Exception as e:
            print(f"⚠️ Lỗi đọc {DATA_FILE}: {e}", flush=True)

    print("=" * 60, flush=True)
    print(f"🚀 CẬP NHẬT GIÁ REALTIME — {len(symbols)} mã", flush=True)
    print("=" * 60, flush=True)

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    count_success = 0
    count_fail = 0

    for i, sym in enumerate(symbols, 1):
        print(f"[{i:>3}/{len(symbols)}] Đang lấy {sym:<6} ...", end="", flush=True)
        
        close_price = fetch_price_with_timeout(sym, timeout=8)
        
        if close_price > 0:
            # lotusmarket trả về giá dạng VND (VD: 20350), ta giữ nguyên
            if close_price < 1000:
                close_price = close_price * 1000
            
            if sym not in stock_db:
                stock_db[sym] = {}
                
            stock_db[sym]["close"] = int(close_price)
            stock_db[sym]["updated_at"] = now_str
            
            print(f" ✅ {int(close_price):>10,}", flush=True)
            count_success += 1
        else:
            # Nếu lấy giá thất bại, giữ nguyên giá cũ trong data.json
            old_price = stock_db.get(sym, {}).get("close", 0)
            print(f" ❌ Lỗi (giữ giá cũ: {int(old_price):>,})", flush=True)
            count_fail += 1
            
        # Nghỉ 1 giây để tránh bị VPS chặn IP
        time.sleep(1.0)

    # Ghi lại data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)

    # Ghi lại last_update.json
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update": now_str}, f, ensure_ascii=False, indent=4)

    print("\n" + "=" * 60, flush=True)
    print(f"📊 TỔNG KẾT: {count_success} thành công | {count_fail} thất bại", flush=True)
    print(f"🕒 Mốc thời gian: {now_str}", flush=True)
    print(f"📁 Đã cập nhật: {DATA_FILE}, {LAST_UPDATE_FILE}", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    main()
