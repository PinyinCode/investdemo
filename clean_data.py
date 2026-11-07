import json
import os
import subprocess

# File chứa danh sách mã CHUẨN (Sẽ dùng file này làm gốc để lọc)
MASTER_SYMBOLS_FILE = "vn100_symbols.json"

# Các file cần dọn dẹp (Bao gồm cả vn100_full_info.json)
FILES_TO_CLEAN = [
    "vn100_full_info.json",      # <-- Thêm file này vào danh sách cần dọn
    "screener_results.json",
    "data.json",
    "symbol_sim_rates.json",
    "quarterly_mean_details.json",
    "cheap_stocks.json"
]

COMMIT_MESSAGE = "🧹 Auto-clean invalid symbols (TID, VDP...) from JSON files"

def run_git_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Lỗi Git: {cmd}")
        print(e.stderr)
        return False

def get_master_symbols():
    """Đọc danh sách mã chuẩn từ vn100_symbols.json."""
    if not os.path.exists(MASTER_SYMBOLS_FILE):
        print(f"❌ Không tìm thấy file gốc {MASTER_SYMBOLS_FILE}.")
        return None
    
    try:
        with open(MASTER_SYMBOLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        valid_symbols = set()
        for item in data:
            if isinstance(item, str):
                valid_symbols.add(item.strip().upper())
            elif isinstance(item, dict) and "symbol" in item:
                valid_symbols.add(item["symbol"].strip().upper())
                
        print(f"✅ Đã tải {len(valid_symbols)} mã chuẩn từ {MASTER_SYMBOLS_FILE}.")
        return valid_symbols
    except Exception as e:
        print(f"❌ Lỗi đọc {MASTER_SYMBOLS_FILE}: {e}")
        return None

def clean_file(filename, valid_symbols):
    """Dọn dẹp một file, chỉ giữ lại các mã có trong valid_symbols."""
    if not os.path.exists(filename):
        print(f"⏭️ Bỏ qua {filename} (không tồn tại).")
        return False
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file {filename}: {e}")
        return False

    removed_count = 0
    removed_names = []

    # Dạng List (screener_results, vn100_full_info nếu là list...)
    if isinstance(data, list):
        new_data = []
        for item in data:
            sym = ""
            if isinstance(item, dict):
                sym = item.get("symbol", "").strip().upper()
            elif isinstance(item, str):
                sym = item.strip().upper()
                
            if sym in valid_symbols:
                new_data.append(item)
            else:
                removed_count += 1
                if len(removed_names) < 5: removed_names.append(sym)
        data = new_data

    # Dạng Dict
    elif isinstance(data, dict):
        first_key = next(iter(data), "").upper()
        
        # Kiểm tra xem đây là dict của các mã (data.json) hay dict của các nhóm ngành (cheap_stocks.json)
        if first_key in valid_symbols or (first_key.isalnum() and len(first_key) <= 5):
            # Dạng {"VCB": {...}, "TID": {...}}
            for sym in list(data.keys()):
                if sym.strip().upper() not in valid_symbols:
                    del data[sym]
                    removed_count += 1
                    if len(removed_names) < 5: removed_names.append(sym)
        else:
            # Dạng {"SECTOR": [ {...}, {...} ]} (cheap_stocks)
            for sector, stocks in data.items():
                if isinstance(stocks, list):
                    new_stocks = []
                    for stock in stocks:
                        sym = stock.get("symbol", "").strip().upper() if isinstance(stock, dict) else str(stock).strip().upper()
                        if sym in valid_symbols:
                            new_stocks.append(stock)
                        else:
                            removed_count += 1
                            if len(removed_names) < 5: removed_names.append(sym)
                    data[sector] = new_stocks

    if removed_count > 0:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"🧹 {filename}: Đã xoá {removed_count} mã rác {removed_names if removed_count <= 5 else '...'}")
            return True
        except Exception as e:
            print(f"❌ Lỗi ghi file {filename}: {e}")
            return False
    else:
        print(f"✨ {filename}: Sạch, không có mã rác.")
        return False

def main():
    print("🚀 Bắt đầu quá trình dọn dẹp dữ liệu...")
    
    # 1. Lấy danh sách mã chuẩn
    valid_symbols = get_master_symbols()
    if not valid_symbols:
        return

    # 2. Dọn dẹp từng file
    has_changes = False
    for filename in FILES_TO_CLEAN:
        if clean_file(filename, valid_symbols):
            has_changes = True
            
    if not has_changes:
        print("\n✅ Không có file nào cần dọn dẹp. Không cần push Git.")
        return
        
    # 3. Git add, commit, push
    print("\n📦 Đang tự động đẩy lên GitHub...")
    run_git_command("git add .")
    
    commit_ok = run_git_command(f'git commit -m "{COMMIT_MESSAGE}"')
    
    if commit_ok:
        run_git_command("git pull --rebase origin main")
        run_git_command("git push origin main")
        print("\n🎉 Đã push thành công lên GitHub!")
    else:
        print("\n⚠️ Không có thay đổi nào để commit.")

if __name__ == "__main__":
    main()
