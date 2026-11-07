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
REALTIME_META_FILE = "realtime_meta.json"


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

    print("=" * 70)
    print(f"🔄 CẬP NHẬT REALTIME — {len(symbols)} mã")
    print("=" * 70)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    ok_list = []        # mã cập nhật thành công
    fail_list = []      # mã thất bại (kèm lý do)
    skip_list = []      # mã không có trong data.json
    unchanged_list = [] # mã lấy được nhưng giá không đổi

    for i, symbol in enumerate(symbols, 1):
        realtime, err = fetch_realtime(symbol)

        # ---------- THẤT BẠI ----------
        if realtime is None:
            fail_list.append((symbol, err))
            print(f"[{i:>3}/{len(symbols)}] ❌ {symbol:<6} — {err}")
            time.sleep(0.15)
            continue

        # ---------- KHÔNG CÓ TRONG data.json ----------
        if symbol not in stock_db:
            skip_list.append(symbol)
            print(f"[{i:>3}/{len(symbols)}] ⚠️  {symbol:<6} — không có trong data.json")
            time.sleep(0.15)
            continue

        # ---------- THÀNH CÔNG ----------
        old_close = stock_db[symbol].get("close", 0)
        new_close = realtime["close"]

        # Tự động phát hiện đơn vị: nếu < 1000 thì là nghìn VND → *1000
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
            print(f"[{i:>3}/{len(symbols)}] ⚪ {symbol:<6} — {new_close_int:>10,} (không đổi)")
        else:
            arrow = "📈" if diff > 0 else "📉"
            print(f"[{i:>3}/{len(symbols)}] ✅ {symbol:<6} — {old_close:>10,} → {new_close_int:>10,} ({diff_pct:+.2f}%) {arrow}")
            ok_list.append((symbol, old_close, new_close_int, diff_pct))

        time.sleep(0.15)

    # ---------- GHI data.json ----------
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)

    # ---------- GHI last_update.json (đúng định dạng bạn muốn) ----------
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update": now_str}, f, ensure_ascii=False, indent=4)

    # ---------- GHI realtime_meta.json (log chi tiết) ----------
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

    # ---------- TỔNG KẾT ----------
    print("\n" + "=" * 70)
    print("📊 TỔNG KẾT")
    print("=" * 70)
    print(f"✅ Cập nhật có thay đổi : {len(ok_list):>3} mã")
    print(f"⚪ Không đổi giá        : {len(unchanged_list):>3} mã")
    print(f"❌ Thất bại             : {len(fail_list):>3} mã")
    print(f"⚠️  Bỏ qua (không có)   : {len(skip_list):>3} mã")
    print(f"🕒 Mốc thời gian        : {now_str}")

    if ok_list:
        print("\n📈 DANH SÁCH MÃ ĐÃ CẬP NHẬT (có thay đổi giá):")
        for sym, o, n, p in ok_list:
            print(f"   • {sym:<6}  {o:>10,} → {n:>10,}  ({p:+.2f}%)")

    if fail_list:
        print("\n❌ DANH SÁCH MÃ THẤT BẠI:")
        for sym, reason in fail_list:
            print(f"   • {sym:<6}  — {reason}")

    if skip_list:
        print("\n⚠️  DANH SÁCH MÃ KHÔNG CÓ TRONG data.json:")
        print(f"   {', '.join(skip_list)}")

    print("=" * 70)
    print(f"📁 Đã ghi đè: {DATA_FILE}, {LAST_UPDATE_FILE}, {REALTIME_META_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
