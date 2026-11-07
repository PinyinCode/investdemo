import os
import json
import time
import sys
from datetime import datetime

try:
    from lotusmarket import fetchers
except ImportError:
    print("❌ Thiếu thư viện. Cài đặt: pip install lotusmarket[fetchers]", flush=True)
    sys.exit(1)

DATA_FILE = "data.json"
LAST_UPDATE_FILE = "last_update.json"
REALTIME_META_FILE = "realtime_meta.json"

def get_symbols_from_data():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Không tìm thấy {DATA_FILE}", flush=True)
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return list(data.keys())
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e}", flush=True)
        return []

def fetch_realtime(symbol):
    try:
        stock = fetchers.vps(symbol)
        close_val = getattr(stock, "close", None)
        volume_val = getattr(stock, "volume", None)

        if close_val is None:
            return None, "không có trường close"

        return {
            "close": float(close_val),
            "volume": int(volume_val) if volume_val is not None else None,
        }, None
    except Exception as e:
        return None, str(e)

def main():
    symbols = get_symbols_from_data()
    if not symbols:
        return

    print("=" * 70, flush=True)
    print(f"🔄 CẬP NHẬT REALTIME — {len(symbols)} mã", flush=True)
    print("=" * 70, flush=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    ok_list = []        
    fail_list = []      
    skip_list = []      
    unchanged_list = [] 

    for i, symbol in enumerate(symbols, 1):
        # In ra trước khi gọi API để biết nó đang xử lý mã nào
        print(f"[{i:>3}/{len(symbols)}] Đang lấy {symbol:<6} ...", end="", flush=True)
        
        realtime, err = fetch_realtime(symbol)

        if realtime is None:
            fail_list.append((symbol, err))
            print(f" ❌ Lỗi: {err}", flush=True)
            time.sleep(0.15)
            continue

        if symbol not in stock_db:
            skip_list.append(symbol)
            print(f" ⚠️ Không có trong data.json", flush=True)
            time.sleep(0.15)
            continue

        old_close = stock_db[symbol].get("close", 0)
        new_close = realtime["close"]

        if new_close < 1000:
            new_close = new_close * 1000
        new_close_int = int(new_close)

        stock_db[symbol]["close"] = new_close_int
        if realtime["volume"] is not None:
            stock_db[symbol]["volume"] = realtime["volume"]
        stock_db[symbol]["realtime_updated"] = now_str

        diff = new_close_int - old_close
        diff_pct = (diff / old_close * 100) if old_close else 0

        if diff == 0:
            unchanged_list.append(symbol)
            print(f" ⚪ {new_close_int:>10,} (không đổi)", flush=True)
        else:
            arrow = "📈" if diff > 0 else "📉"
            print(f" ✅ {old_close:>10,} → {new_close_int:>10,} ({diff_pct:+.2f}%) {arrow}", flush=True)
            ok_list.append((symbol, old_close, new_close_int, diff_pct))

        time.sleep(0.15)

    # Ghi file
    print("\n💾 Đang ghi đè các file JSON...", flush=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)

    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update": now_str}, f, ensure_ascii=False, indent=4)

    realtime_meta = {
        "realtime_last_update": now_str,
        "total_symbols": len(symbols),
        "updated_count": len(ok_list),
        "unchanged_count": len(unchanged_list),
        "failed_count": len(fail_list),
        "skipped_count": len(skip_list),
        "updated_symbols": [s for s, _, _, _ in ok_list],
        "unchanged_symbols": unchanged_list,
        "failed_symbols": [{"symbol": s, "reason": r} for s, r in fail_list],
        "skipped_symbols": skip_list,
    }
    with open(REALTIME_META_FILE, "w", encoding="utf-8") as f:
        json.dump(realtime_meta, f, ensure_ascii=False, indent=4)

    print("\n" + "=" * 70, flush=True)
    print(f"📊 TỔNG KẾT: {len(ok_list)} cập nhật | {len(unchanged_list)} không đổi | {len(fail_list)} lỗi", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
