import os
import sys
from pymongo import MongoClient

def fix_prices():
    # Lấy URI từ biến môi trường của Github Secrets
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("❌ LỖI: Thiếu biến môi trường MONGO_URI!")
        sys.exit(1)

    print("🔌 Đang kết nối MongoDB...")
    try:
        client = MongoClient(mongo_uri)
        db = client['quant_db']
        collection = db['stocks']
        
        # Lấy tất cả các mã
        all_stocks = list(collection.find({}))
        print(f"📊 Tìm thấy {len(all_stocks)} mã trong DB.")

        updated_count = 0
        for doc in all_stocks:
            update_data = {}
            
            # Chỉ xử lý nếu giá close >= 1000 (tức là đang bị lưu đơn vị Đồng)
            if doc.get("close", 0) >= 1000:
                for field in ["close", "open", "high", "low", "prev_close"]:
                    val = doc.get(field, 0)
                    if val and val >= 1000:
                        # Chia 1000 và làm tròn 2 chữ số thập phân (VD: 11.9)
                        update_data[field] = round(val / 1000.0, 2)
                
                if update_data:
                    collection.update_one({"_id": doc["_id"]}, {"$set": update_data})
                    updated_count += 1
                    print(f"✅ Đã sửa {doc['symbol']}: {doc.get('close')} -> {update_data.get('close')}")
            else:
                print(f"⏭️ Bỏ qua {doc.get('symbol')} (Giá đã chuẩn: {doc.get('close')})")

        print(f"\n🎉 HOÀN TẤT! Đã cập nhật {updated_count} mã về đơn vị Nghìn đồng.")

    except Exception as e:
        print(f"❌ Lỗi kết nối hoặc cập nhật: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_prices()
