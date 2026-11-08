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

# ============================================================
# HÀM TỰ ĐỘNG DỊCH NGÀNH TỪ TIẾNG ANH SANG TIẾNG VIỆT
# ============================================================
def translate_sector(sector_name):
    if not sector_name:
        return "SAN_XUAT_TIEU_DUNG_PHONG_THU"
        
    mapping = {
        "BANKS": "NGAN_HANG",
        "FINANCIALS": "CHUNG_KHOAN",
        "SECURITIES": "CHUNG_KHOAN",
        "REAL ESTATE": "BAT_DONG_SAN",
        "REAL_ESTATE": "BAT_DONG_SAN",
        "TECHNOLOGY": "CONG_NGHE_BAN_LE",
        "RETAIL": "CONG_NGHE_BAN_LE",
        "UTILITIES": "DIEN_NUOC_HA_TANG",
        "ENERGY": "DIEN_NUOC_HA_TANG",
        "MATERIALS": "NGUYEN_VAT_LIEU_CHU_KY",
        "INDUSTRIALS": "NGUYEN_VAT_LIEU_CHU_KY",
        "CONSUMER STAPLES": "SAN_XUAT_TIEU_DUNG_PHONG_THU",
        "CONSUMER DISCRETIONARY": "SAN_XUAT_TIEU_DUNG_PHONG_THU",
        "HEALTHCARE": "SAN_XUAT_TIEU_DUNG_PHONG_THU"
    }
    upper_name = str(sector_name).upper()
    for eng, vn in mapping.items():
        if eng in upper_name:
            return vn
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"

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
            
            # LẤY THÊM THÔNG TIN NGÀNH
            raw_sector = row.get('sector', '')
            vn_sector = translate_sector(raw_sector)
            
            return company_name, close_price, total_shares, vn_sector
    except Exception:
        pass
    return symbol, 0, 0, "SAN_XUAT_TIEU_DUNG_PHONG_THU"

def get_company_info_with_timeout(symbol, timeout=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fetch_company_overview, symbol)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return symbol, 0, 0, "SAN_XUAT_TIEU_DUNG_PHONG_THU"
        except Exception:
            return symbol, 0, 0, "SAN_XUAT_TIEU_DUNG_PHONG_THU"

def auto_git_push():
    try:
        print(f"\n📤 Đang tự động đồng bộ file {OUTPUT_FILE} lên GitHub...")
        
        subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True)
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

        commit_msg = f"Auto update company info - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
        print("🚀 Đẩy dữ liệu lên GitHub thành công!")
        
    except subprocess.CalledProcessError as e:
        error_msg = str(e.output) if e.output else str(e)
        if "nothing to commit" not in error_msg:
            print(f"⚠️ Lỗi Git push: {error_msg}")
    except Exception as e:
        print(f"⚠️ Lỗi không xác định: {e}")

def print_symbol_list(symbols):
    """In danh sách mã kèm STT để người dùng dễ chọn"""
    print("\n📋 DANH SÁCH MÃ VÀ SỐ THỨ TỰ:")
    for i in range(0, len(symbols), 4):
        row_str = ""
        for j in range(4):
            if i + j < len(symbols):
                stt = i + j + 1
                sym = symbols[i + j]
                row_str += f"{stt:>3}. {sym:<6}   "
        print(row_str)
    print()

def main():
    print("==================================================")
    print("      CÀO THÔNG TIN DOANH NGHIỆP VN100 (TÊN, SLCP, NGÀNH)  ")
    print("==================================================")
    
    if not os.path.exists(SYMBOLS_FILE):
        print(f"❌ Không tìm thấy {SYMBOLS_FILE}.")
        return
        
    with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
        all_symbols = json.load(f)

    old_data = get_old_data()
    # Kiểm tra xem mã nào đã có total_shares > 0 (coi như đã cào thành công)
    crawled_symbols = [sym for sym, data in old_data.items() if data.get("total_shares", 0) > 0]
    
    print(f"📊 Trạng thái hiện tại: Đã cào được {len(crawled_symbols)}/{len(all_symbols)} mã.")
    print("1. Cào TIẾP (Chỉ lấy những mã chưa có trong file)")
    print("2. Cào LẠI TỪ ĐẦU (Xóa file cũ, cào lại 100 mã)")
    print("3. Cào CÁC MÃ CỤ THỂ (Nhập 1 hoặc nhiều mã, cách nhau bởi dấu phẩy)")
    print("4. Cào THEO SỐ THỨ TỰ (VD: Từ STT 1 đến STT 30)")
    
    choice = input("Nhập lựa chọn của bạn (1/2/3/4, mặc định 1): ").strip()
    
    symbols_to_crawl = []
    
    if choice == '2':
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
            old_data = {}
        symbols_to_crawl = all_symbols
        print("🔄 Đã xóa dữ liệu cũ. Sẽ cào lại từ đầu.")
        
    elif choice == '3':
        raw_symbols = input("Nhập các mã muốn cào (VD: FPT, ANV, HPG): ").strip().upper()
        if raw_symbols:
            input_list = [s.strip() for s in raw_symbols.split(",") if s.strip()]
            symbols_to_crawl = list(dict.fromkeys(input_list))
            print(f"🎯 Sẽ cào riêng {len(symbols_to_crawl)} mã: {', '.join(symbols_to_crawl)}")
        else:
            print("❌ Không nhận được mã. Thoát.")
            return
            
    elif choice == '4':
        print_symbol_list(all_symbols)
        try:
            start_str = input(f"Nhập STT bắt đầu (1 - {len(all_symbols)}): ").strip()
            end_str = input(f"Nhập STT kết thúc (1 - {len(all_symbols)}): ").strip()
            
            start_idx = int(start_str) - 1
            end_idx = int(end_str)  
            
            if start_idx < 0 or end_idx > len(all_symbols) or start_idx >= end_idx:
                print("❌ Khoảng STT không hợp lệ. Thoát.")
                return
                
            symbols_to_crawl = all_symbols[start_idx:end_idx]
            print(f"🎯 Sẽ cào {len(symbols_to_crawl)} mã từ STT {start_str} đến {end_str}.")
        except ValueError:
            print("❌ Bạn phải nhập số. Thoát.")
            return
    else:
        symbols_to_crawl = [s for s in all_symbols if s not in crawled_symbols]
        print(f"⏩ Sẽ cào tiếp {len(symbols_to_crawl)} mã còn lại.")

    if not symbols_to_crawl:
        print("🎉 Tất cả các mã đã được cào xong!")
        return
        
    print(f"\n🚀 Bắt đầu xử lý {len(symbols_to_crawl)} mã...\n")
    
    count_success = 0
    count_fail_consecutive = 0
    
    for i, sym in enumerate(symbols_to_crawl, 1):
        print(f"[{i}/{len(symbols_to_crawl)}] Đang lấy {sym:<6} ...", end="", flush=True)
        
        company_name, close_price, total_shares, vn_sector = get_company_info_with_timeout(sym, timeout=10)

        if total_shares == 0:
            print(f" ❌ Bị lỗi/khóa IP")
            count_fail_consecutive += 1
            
            if count_fail_consecutive >= 3:
                print("\n🚨 BỊ KHÓA IP! Đã lỗi 3 lần liên tiếp. Dừng script để bảo vệ dữ liệu.")
                print("👉 Hãy tắt/bật lại Modem mạng (hoặc dùng 4G), sau đó chạy lại script để cào tiếp.")
                break
                
            time.sleep(15)
            continue

        count_fail_consecutive = 0
        count_success += 1

        # CẬP NHẬT THÊM TRƯỜNG "sector" VÀO DỮ LIỆU
        old_data[sym] = {
            "symbol": sym,
            "company_name": company_name,
            "total_shares": total_shares,
            "close_price": int(close_price),
            "sector": vn_sector
        }

        result = sorted(list(old_data.values()), key=lambda x: x["symbol"])
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        shares_million = total_shares / 1_000_000
        print(f" ✅ {company_name[:15]}... | Ngành: {vn_sector:<12} | SLCP: {shares_million:,.1f} tr")

        time.sleep(3) 

    if count_success > 0:
        auto_git_push()
    else:
        print("\n⚠️ Không có mã mới nào được cào thành công nên không Git push.")

if __name__ == "__main__":
    main()
