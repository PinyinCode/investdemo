import os
import sys
import pymongo
from datetime import datetime, timedelta

# ===================== CẤU HÌNH =====================
# Script sẽ tự động lấy MONGO_URI từ biến môi trường (Environment Variable)
MONGO_URI = os.environ.get("MONGO_URI", "").strip()

if not MONGO_URI:
    print("❌ LỖI: Không tìm thấy biến môi trường MONGO_URI.")
    print("Vui lòng thiết lập MONGO_URI trước khi chạy script này.")
    sys.exit(1)

def get_trading_date():
    """Lấy ngày giao dịch (nếu trước 9h sáng thì coi là ngày hôm qua)"""
    vn_now = datetime.utcnow() + timedelta(hours=7)
    if vn_now.hour < 9: 
        vn_now -= timedelta(days=1)
    while vn_now.weekday() >= 5: 
        vn_now -= timedelta(days=1)
    return vn_now.strftime("%Y-%m-%d")

def main():
    print("🔌 Đang kết nối MongoDB...")
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Kết nối MongoDB thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        sys.exit(1)
        
    db = client["quant_db"]
    collection = db["stocks"]
    history_col = db["history_data"]
    
    trading_date = get_trading_date()
    print(f"📅 Ngày giao dịch hiện tại (theo logic): {trading_date}")
    
    all_symbols = [doc["symbol"] for doc in collection.find({}, {"symbol": 1})]
    print(f"🔍 Tìm thấy {len(all_symbols)} mã. Bắt đầu sửa dữ liệu...\n")
    
    updated_count = 0
    skipped_count = 0
    
    for sym in all_symbols:
        doc = collection.find_one({"symbol": sym})
        if not doc or "close" not in doc:
            skipped_count += 1
            continue
            
        close_price = float(doc["close"])
        hist_doc = history_col.find_one({"symbol": sym})
        
        prev_close = 0.0
        if hist_doc and hist_doc.get("history_d1"):
            bars = hist_doc["history_d1"]
            # Sắp xếp nến từ cũ đến mới
            bars_sorted = sorted(bars, key=lambda x: x.get("time", ""))
            
            # Tìm nến gần nhất có ngày nhỏ hơn trading_date (tức là nến hôm qua)
            for b in reversed(bars_sorted):
                b_time = b.get("time")
                if b_time and b_time < trading_date:
                    prev_close = float(b["close"])
                    break
        
        if prev_close <= 0:
            print(f"  ⚠️ {sym}: Không có nến hôm qua trong DB. Bỏ qua.")
            skipped_count += 1
            continue
            
        pct_change = round(((close_price - prev_close) / prev_close) * 100, 2)
        
        arrow, color = "—", "slate"
        if pct_change > 0: arrow, color = "▲", "emerald"
        elif pct_change < 0: arrow, color = "▼", "rose"
        
        # Cập nhật lại DB
        collection.update_one({"symbol": sym}, {"$set": {
            "prev_close": prev_close,
            "price_change_percent": pct_change,
            "price_change_available": True,
            "price_arrow": arrow,
            "price_color": color
        }})
        
        updated_count += 1
        print(f"  ✅ {sym}: Prev={prev_close} | Close={close_price} | {pct_change:+.2f}% {arrow}")
        
    print(f"\n🎉 Hoàn tất! Đã cập nhật {updated_count} mã. Bỏ qua {skipped_count} mã không đủ dữ liệu.")

if __name__ == "__main__":
    main()
