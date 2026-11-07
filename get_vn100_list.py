import json
from vnstock import Listing

SYMBOLS_FILE = "vn100_symbols.json"

def get_vn100_symbols():
    print("🔄 Đang lấy danh sách mã VN100 từ VCI...", flush=True)
    try:
        listing = Listing(source='VCI')
        data = listing.symbols_by_group('VN100')
        
        if data is not None:
            symbols = []
            # Xử lý linh hoạt tùy theo định dạng vnstock trả về (DataFrame, Series, List)
            if hasattr(data, 'columns'):
                col_name = 'symbol' if 'symbol' in data.columns else ('ticker' if 'ticker' in data.columns else data.columns[0])
                symbols = data[col_name].astype(str).tolist()
            elif hasattr(data, 'values'):
                symbols = data.astype(str).tolist()
            elif isinstance(data, list):
                symbols = [str(x) for x in data]
            
            # Loại bỏ trùng lặp và sắp xếp A-Z
            symbols = sorted(list(set(symbols)))
            
            if symbols:
                # Lưu ra file JSON
                with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
                    json.dump(symbols, f, ensure_ascii=False, indent=4)
                print(f"✅ Đã lấy và lưu thành công {len(symbols)} mã vào file {SYMBOLS_FILE}")
                return symbols
            else:
                print("⚠️ Danh sách trả về bị rỗng.")
        else:
            print("⚠️ Không có dữ liệu trả về.")
            
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách VN100: {e}")
        
    return []

if __name__ == "__main__":
    get_vn100_symbols()
