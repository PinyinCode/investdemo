import json
import os

# Danh sách các file cần dọn dẹp
FILES_TO_CLEAN = [
    "screener_results.json",
    "data.json",
    "symbol_sim_rates.json",
    "quarterly_mean_details.json",
    "cheap_stocks.json" # Nếu file này có cấu trúc khác, sẽ xử lý riêng bên dưới
]

SYMBOLS_FILE = "vn100_symbols.json"

def load_vn100_symbols():
    """Đọc danh sách mã hợp lệ từ vn100_symbols.json"""
    if not os.path.exists(SYMBOLS_FILE):
        print(f"❌ Không tìm thấy file {SYMBOLS_FILE}. Dừng chương trình.")
        return None
    
    try:
        with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        valid_symbols = set()
        for item in data:
            if isinstance(item, str):
                valid_symbols.add(item.strip().upper())
            elif isinstance(item, dict) and "symbol" in item:
                valid_symbols.add(item["symbol"].strip().upper())
                
        print(f"✅ Đã tải {len(valid_symbols)} mã hợp lệ từ {SYMBOLS_FILE}")
        return valid_symbols
    except Exception as e:
        print(f"❌ Lỗi đọc {SYMBOLS_FILE}: {e}")
        return None

def clean_file(filename, valid_symbols):
    """Dọn dẹp một file JSON cụ thể."""
    if not os.path.exists(filename):
        print(f"⏭️ Bỏ qua {filename} (không tồn tại).")
        return

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file {filename}: {e}")
        return

    original_count = 0
    removed_count = 0

    # TRƯỜNG HỢP 1: File có dạng LIST (ví dụ: screener_results.json)
    if isinstance(data, list):
        original_count = len(data)
        new_data = []
        removed_symbols = []
        for item in data:
            sym = item.get("symbol", "").strip().upper() if isinstance(item, dict) else ""
            if sym in valid_symbols:
                new_data.append(item)
            else:
                removed_count += 1
                removed_symbols.append(sym)
        
        data = new_data
        print(f"🧹 {filename}: Đã xoá {removed_count} mã lỗi {removed_symbols if removed_count < 10 else '(quá nhiều)'}")

    # TRƯỜNG HỢP 2: File có dạng DICT (ví dụ: data.json)
    elif isinstance(data, dict):
        original_count = len(data)
        
        # Kiểm tra xem đây có phải là dict của các mã cổ phiếu không
        # (Dựa vào việc key đầu tiên có phải là mã hợp lệ không)
        first_key = next(iter(data), "").upper()
        
        if first_key in valid_symbols or first_key.isalnum():
            # data.json dạng: { "VCB": {...}, "TID": {...} }
            removed_symbols = []
            for sym in list(data.keys()):
                if sym.strip().upper() not in valid_symbols:
                    del data[sym]
                    removed_count += 1
                    removed_symbols.append(sym)
            print(f"🧹 {filename}: Đã xoá {removed_count} mã lỗi {removed_symbols if removed_count < 10 else '(quá nhiều)'}")
            
        else:
            # cheap_stocks.json dạng: { "SECTOR_NAME": [ {...}, {...} ] }
            removed_symbols = []
            for sector, stocks in data.items():
                if isinstance(stocks, list):
                    new_stocks = []
                    for stock in stocks:
                        sym = stock.get("symbol", "").strip().upper() if isinstance(stock, dict) else str(stock).strip().upper()
                        if sym in valid_symbols:
                            new_stocks.append(stock)
                        else:
                            removed_count += 1
                            removed_symbols.append(sym)
                    data[sector] = new_stocks
            print(f"🧹 {filename}: Đã xoá {removed_count} mã lỗi khỏi các nhóm ngành")

    # Ghi lại file nếu có thay đổi
    if removed_count > 0:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"💾 Đã lưu lại {filename} (Còn {original_count - removed_count} mã).")
        except Exception as e:
            print(f"❌ Lỗi ghi file {filename}: {e}")
    else:
        print(f"✨ {filename}: Sạch, không có mã lỗi nào.")

def main():
    print("🚀 Bắt đầu quá trình dọn dẹp dữ liệu...")
    valid_symbols = load_vn100_symbols()
    if not valid_symbols:
        return

    for filename in FILES_TO_CLEAN:
        clean_file(filename, valid_symbols)
        
    print("\n✅ HOÀN TẤT DỌN DẸP!")

if __name__ == "__main__":
    main()
