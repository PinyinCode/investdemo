from pymongo import MongoClient
import os

MONGO_URI = "dán_link_mongo_cua_ban_vao_day"
client = MongoClient(MONGO_URI)
db = client['quant_db']
collection = db['stocks']

# Tìm các mã có giá > 1000 (tức là đang bị lưu bằng đồng) và chia lại cho 1000
docs = collection.find({"close": {"$gte": 1000}})
count = 0
for doc in docs:
    update_data = {}
    for field in ["close", "open", "high", "low", "prev_close"]:
        if field in doc and doc[field] >= 1000:
            update_data[field] = doc[field] / 1000.0
            
    if update_data:
        collection.update_one({"_id": doc["_id"]}, {"$set": update_data})
        count += 1

print(f"Đã sửa lại đơn vị cho {count} mã!")
