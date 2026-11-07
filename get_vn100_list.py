import json
import os
import subprocess
import datetime
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

def auto_git_push_symbols():
    """Tự động đẩy file symbols lên GitHub"""
    try:
        print(f"\n📤 Đang tự động đồng bộ file {SYMBOLS_FILE} lên GitHub...")
        
        # Đồng bộ với remote
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        pull_result = subprocess.run(
            ["git", "pull", "origin", "main", "--rebase", "--autostash"], 
            capture_output=True, text=True
        )
        if pull_result.returncode != 0:
            print("⚠️ Có xung đột khi pull, hủy rebase để ưu tiên file dưới máy...")
            subprocess.run(["git", "rebase", "--abort"], check=False)

        # Thêm file vào git
        subprocess.run(["git", "add", SYMBOLS_FILE], check=True)
        
        # Kiểm tra xem có thay đổi không
        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("ℹ️ Không có dữ liệu danh sách nào thay đổi để đẩy lên.")
            return

        # Commit và Push
        commit_msg = f"Auto update {SYMBOLS_FILE} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy danh sách lên GitHub thành công!")
        
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

if __name__ == "__main__":
    symbols = get_vn100_symbols()
    # Nếu lấy được danh sách thành công thì mới push lên Git
    if symbols:
        auto_git_push_symbols()
