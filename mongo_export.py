import os
import json
import pymongo
from datetime import datetime

# Lấy thông tin từ biến môi trường (GitHub Secrets truyền vào)
MONGO_URI = os.environ.get("MONGO_URI")

# Đã điền chính xác tên DB và Collection từ ảnh bạn gửi
DB_NAME = os.environ.get("DB_NAME", "quant_db") 
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "history_data") 

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "history_export.json")

def export_mongo_data():
    if not MONGO_URI:
        print("❌ Lỗi: Không tìm thấy biến môi trường MONGO_URI. Hãy kiểm tra lại GitHub Secrets.")
        exit(1)

    print(f"⏳ Đang kết nối tới MongoDB (DB: {DB_NAME}, Collection: {COLLECTION_NAME})...")
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        
        # Kiểm tra kết nối
        client.server_info() 
        print("✅ Kết nối thành công!")

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Lấy toàn bộ dữ liệu, bỏ trường '_id' (ObjectId) vì nó không serialize được ra JSON chuẩn
        # Sắp xếp theo thời gian giảm dần (nếu có trường thời gian)
        cursor = collection.find({}, {'_id': 0}).sort("_id", -1)
        data = list(cursor)

        print(f"📦 Đã tìm thấy {len(data)} bản ghi.")

        if len(data) == 0:
            print("⚠️ Cảnh báo: Collection đang trống, không có gì để lưu.")
            return

        # Tạo thư mục nếu chưa có
        os.makedirs(DATA_DIR, exist_ok=True)

        # Lưu ra file JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "total_records": len(data),
                "data": data
            }, f, ensure_ascii=False, indent=4)
            
        print(f"💾 Đã lưu dữ liệu thành công vào {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Lỗi khi kết nối hoặc lấy dữ liệu từ MongoDB: {e}")
        exit(1) # Báo lỗi để GitHub Actions dừng lại và báo đỏ

if __name__ == "__main__":
    export_mongo_data()
