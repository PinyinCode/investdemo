import json
import time
import os
import sys
import subprocess
import datetime
import concurrent.futures
from vnstock import Company

OUTPUT_FILE = "vn100_full_info.json"
SYMBOLS_FILE = "vn100_symbols.json"
PROGRESS_FILE = "crawl_progress.json" # File lưu tiến độ cào

def get_old_data():
    old_data = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data_list = json.load(f)
                for item in data_list:
                    old_data[item["symbol"]] = item
        except Exception:
            pass
    return old_data

def fetch_company_overview(symbol):
    try:
        comp = Company(symbol=symbol, source='VCI')
        df = comp.overview()
        if df is not None and not df.empty:
            row = df.iloc[0]
            company_name = str(row.get('organ_name', symbol))
            close_price = float(row.get('current_price', 0) or 0)
            total_shares = int(float(row.get('issue_share', 0) or 0))
            market_cap = int(float(row.get('market_cap', 0) or 0))
            return company_name, close_price, total_shares, market_cap
    except Exception:
        pass
    return symbol, 0, 0, 0

def get_company_info_with_timeout(symbol, timeout=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fetch_company_overview, symbol)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return symbol, 0, 0, 0
        except Exception:
            return symbol, 0, 0, 0

def auto_git_push():
    """Tự động đẩy file lên GitHub"""
    try:
        print(f"\n📤 Đang tự động đồng bộ file lên GitHub...")
        
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        pull_result = subprocess.run(
            ["git", "pull", "origin", "main", "--rebase", "--autostash"], 
            capture_output=True, text=True
        )
        if pull_result.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], check=False)

        subprocess.run(["git", "add", OUTPUT_FILE], check=True)
        
        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("ℹ️ Không có dữ liệu mới để đẩy lên.")
            return

        commit_msg = f"Auto update VN100 full info - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy dữ liệu lên GitHub thành công!")
        
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

def main():
    # 1. Đọc danh sách VN100
    if not os.path.exists(SYMBOLS_FILE):
        print(f"❌ Không tìm thấy {SYMBOLS_FILE}. Hãy chạy script lấy danh sách trước.")
        return
        
    with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
        all_symbols = json.load(f)

    # 2. Đọc tiến độ cào (Để chạy tiếp nếu bị ngắt)
    old_data = get_old_data()
    
    # Lấy danh sách các mã đã cào thành công (có giá > 0)
    crawled_symbols = [sym for sym, data in old_data.items() if data.get("close_price", 0) > 0]
    
    # Lọc ra các mã chưa cào
    symbols_to_crawl = [s for s in all_symbols if s not in crawled_symbols]
    
    if not symbols_to_crawl:
        print("🎉 Tất cả các mã đã được cào xong từ trước!")
        return
        
    print(f"🚀 Cần cào {len(symbols_to_crawl)} mã (đã bỏ qua {len(crawled_symbols)} mã đã có).")
    
    count = 0
    for sym in symbols_to_crawl:
        count += 1
        print(f"[{count}/{len(symbols_to_crawl)}] Đang lấy {sym:<6} ...", end="", flush=True)
        
        company_name, close_price, total_shares, market_cap = get_company_info_with_timeout(sym, timeout=10)

        if close_price == 0:
            print(f" ❌ Bị lỗi/khóa IP")
            # Nếu lỗi, nghỉ 15s để hồi IP rồi thử lại ở lần chạy sau
            time.sleep(15)
            continue

        # Cập nhật dữ liệu
        old_data[sym] = {
            "symbol": sym,
            "company_name": company_name,
            "market_cap": market_cap,
            "total_shares": total_shares,
            "close_price": int(close_price)
        }

        # Lưu file sau MỖI mã (để không mất dữ liệu nếu có sự cố)
        result = sorted(list(old_data.values()), key=lambda x: x["symbol"])
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        cap_billion = market_cap / 1_000_000_000
        print(f" ✅ {company_name[:20]}... | Vốn hóa: {cap_billion:,.0f} tỷ")

        # --- NGHỈ NGƠI ĐỂ TRÁNH BỊ KHÓA IP ---
        # Nghỉ 3 giây mỗi mã
        time.sleep(3)

    # Cào xong tất cả thì Git Push 1 lần duy nhất
    if count > 0:
        auto_git_push()

if __name__ == "__main__":
    main()
