import os
import json
import pymongo
from datetime import datetime

# Lấy thông tin từ biến môi trường (GitHub Secrets truyền vào)
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "ten_database_cua_ban") # Thay tên DB mặc định của bạn
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "history") # Thay tên collection của bạn

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "history_export.json")

def export_mongo_data():
    if not MONGO_URI:
        print("Lỗi: Không tìm thấy biến môi trường MONGO_URI.")
        return

    print("Đang kết nối tới MongoDB...")
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Kiểm tra kết nối
        client.server_info() 
        print("Kết nối thành công!")

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Lấy toàn bộ dữ liệu, bỏ trường '_id' (ObjectId) vì nó không serialize được ra JSON
        cursor = collection.find({}, {'_id': 0})
        data = list(cursor)

        print(f"Đã tìm thấy {len(data)} bản ghi.")

        # Tạo thư mục nếu chưa có
        os.makedirs(DATA_DIR, exist_ok=True)

        # Lưu ra file JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "total_records": len(data),
                "data": data
            }, f, ensure_ascii=False, indent=4)
            
        print(f"Đã lưu dữ liệu vào {OUTPUT_FILE}")

    except Exception as e:
        print(f"Lỗi khi kết nối hoặc lấy dữ liệu từ MongoDB: {e}")
        exit(1) # Báo lỗi để GitHub Actions dừng lại

if __name__ == "__main__":
    export_mongo_data()
