from lotusmarket import fetchers
try:
    stock = fetchers.vps("ACB")
    print("Thành công! Giá ACB:", stock.close)
except Exception as e:
    print("Bị chặn hoặc lỗi:", e)
