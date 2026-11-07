import os
import json
import time
import sys
from datetime import datetime

try:
    from lotusmarket import fetchers
except ImportError:
    print("❌ Thiếu thư viện. Cài đặt: pip install lotusmarket[fetchers]")
    sys.exit(1)

DATA_FILE = "data.json"
LAST_UPDATE_FILE = "last_update.json"


def get_symbols_from_data():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Không tìm thấy {DATA_FILE}")
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return list(data.keys())
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e}")
        return []


def fetch_realtime(symbol):
    """Lấy giá realtime từ VPS. Trả về dict hoặc None."""
    try:
        stock = fetchers.vps(symbol)
        close_val = getattr(stock, "close", None)
        volume_val = getattr(stock, "volume", None)

        if close_val is None:
            print(f"⚠️ {symbol}: không có trường close")
            return None

        return {
            "close": float(close_val),
            "volume": int(volume_val) if volume_val is not None else None,
        }
    except Exception as e:
        print(f"⚠️ {symbol}: lỗi fetch — {e}")
        return None


def main():
    symbols = get_symbols_from_data()
    if not symbols:
        return

    print(f"🔄 Cập nhật realtime cho {len(symbols)} mã...")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    updated = 0
    failed = 0
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] {symbol}...", end=" ")

        realtime = fetch_realtime(symbol)
        if realtime is None:
            print("❌ bỏ qua")
            failed += 1
            continue

        if symbol in stock_db:
            old_close = stock_db[symbol].get("close", 0)
            new_close = realtime["close"]

            # Tự động phát hiện đơn vị: nếu < 1000 thì là nghìn VND → *1000
            if new_close < 1000:
                new_close = new_close * 1000

            stock_db[symbol]["close"] = int(new_close)

            if realtime["volume"] is not None:
                stock_db[symbol]["volume"] = realtime["volume"]

            stock_db[symbol]["realtime_updated"] = now_str

            diff = new_close - old_close
            diff_pct = (diff / old_close * 100) if old_close else 0
            print(f"✅ {old_close:,} → {int(new_close):,} ({diff_pct:+.1f}%)")
            updated += 1
        else:
            print("⚠️ không có trong data.json")

        time.sleep(0.15)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)

    # Cập nhật mốc thời gian realtime riêng, không đè last_update của crawl
    realtime_meta = {
        "realtime_last_update": now_str,
        "realtime_updated_count": updated,
        "realtime_failed_count": failed,
    }
    with open("realtime_meta.json", "w", encoding="utf-8") as f:
        json.dump(realtime_meta, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Hoàn tất: {updated} mã cập nhật, {failed} mã thất bại.")
    print(f"📁 Đã ghi đè {DATA_FILE} lúc {now_str}")


if __name__ == "__main__":
    main()
