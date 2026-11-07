import json
import os
import subprocess

# Danh sách các file cần dọn dẹp
FILES_TO_CLEAN = [
    "screener_results.json",
    "data.json",
    "symbol_sim_rates.json",
    "quarterly_mean_details.json",
    "cheap_stocks.json"
]

SYMBOLS_FILE = "vn100_symbols.json"
COMMIT_MESSAGE = "🧹 Auto-clean invalid symbols (TID, VDP...) from JSON files"

def run_git_command(cmd):
    """Chạy lệnh Git và in ra kết quả."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Lỗi khi chạy lệnh Git: {cmd}")
        print(e.stderr)
        return False

def load_vn100_symbols():
    if not os.path.exists(SYMBOLS_FILE):
        print(f"❌ Không tìm thấy file {SYMBOLS_FILE}.")
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
    if not os.path.exists(filename):
        return False
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file {filename}: {e}")
        return False

    removed_count = 0
    original_count = 0

    if isinstance(data, list):
        original_count = len(data)
        new_data = []
        for item in data:
            sym = item.get("symbol", "").strip().upper() if isinstance(item, dict) else ""
            if sym in valid_symbols:
                new_data.append(item)
            else:
                removed_count += 1
        data = new_data

    elif isinstance(data, dict):
        original_count = len(data)
        first_key = next(iter(data), "").upper()
        
        if first_key in valid_symbols or first_key.isalnum():
            # data.json
            for sym in list(data.keys()):
                if sym.strip().upper() not in valid_symbols:
                    del data[sym]
                    removed_count += 1
        else:
            # cheap_stocks.json
            for sector, stocks in data.items():
                if isinstance(stocks, list):
                    new_stocks = []
                    for stock in stocks:
                        sym = stock.get("symbol", "").strip().upper() if isinstance(stock, dict) else str(stock).strip().upper()
                        if sym in valid_symbols:
                            new_stocks.append(stock)
                        else:
                            removed_count += 1
                    data[sector] = new_stocks

    if removed_count > 0:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"🧹 {filename}: Đã xoá {removed_count} mã lỗi.")
            return True
        except Exception as e:
            print(f"❌ Lỗi ghi file {filename}: {e}")
            return False
    else:
        print(f"✨ {filename}: Sạch.")
        return False

def main():
    print("🚀 Bắt đầu quá trình dọn dẹp dữ liệu...")
    valid_symbols = load_vn100_symbols()
    if not valid_symbols:
        return

    has_changes = False
    for filename in FILES_TO_CLEAN:
        if clean_file(filename, valid_symbols):
            has_changes = True
            
    if not has_changes:
        print("\n✅ Không có file nào cần dọn dẹp. Không cần push Git.")
        return
        
    print("\n📦 Đang tự động đẩy lên GitHub...")
    run_git_command("git add .")
    
    # Thử commit, nếu không có gì thay đổi thì bỏ qua
    commit_ok = run_git_command(f'git commit -m "{COMMIT_MESSAGE}"')
    
    if commit_ok:
        run_git_command("git pull --rebase origin main")
        run_git_command("git push origin main")
        print("\n🎉 Đã push thành công lên GitHub!")
    else:
        print("\n⚠️ Không có thay đổi nào để commit (có thể file đã được dọn trước đó).")

if __name__ == "__main__":
    main()
