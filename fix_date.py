import os
from pymongo import MongoClient

# LẤY MONGO_URI TỪ GITHUB SECRETS
MONGO_URI = os.environ.get("MONGO_URI", "").strip()

if not MONGO_URI:
    print("❌ LỖI: Thiếu MONGO_URI trong biến môi trường!")
    exit(1)

def fix_trading_date():
    print("🔌 Đang kết nối MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client['quant_db']
    collection = db['stocks']

    # Cập nhật TẤT CẢ các mã đang bị kẹt ngày 09/11 về lại ngày 06/11
    result = collection.update_many(
        {"trading_date": "2026-11-09"}, 
        {"$set": {"trading_date": "2026-11-06"}}
    )

    print(f"✅ Đã sửa thành công {result.modified_count} mã.")

if __name__ == "__main__":
    fix_trading_date()
