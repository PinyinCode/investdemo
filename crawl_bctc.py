import os
import json
import time
import subprocess
import datetime
from vnstock import Fundamental

OUTPUT_DIR = "bctc_data"
SYMBOLS_FILE = "vn100_symbols.json" # File chứa danh sách mã đã cào

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_symbols_from_json():
    """Đọc danh sách mã từ file vn100_symbols.json"""
    if os.path.exists(SYMBOLS_FILE):
        try:
            with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
                symbols = json.load(f)
                if isinstance(symbols, list) and len(symbols) > 0:
                    # Đảm bảo tất cả đều là chữ HOA và không trùng lặp
                    return sorted(list(set([str(s).upper() for s in symbols])))
        except Exception as e:
            print(f"⚠️ Lỗi đọc file {SYMBOLS_FILE}: {e}")
            
    # Fallback: Nếu không có file JSON, quét các file đã cào trong bctc_data
    print("⚠️ Không tìm thấy vn100_symbols.json. Quét thư mục bctc_data...")
    existing_symbols = []
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith(".json"):
                existing_symbols.append(filename.replace(".json", "").upper())
                
    if existing_symbols:
        return sorted(list(set(existing_symbols)))
        
    return []

def fetch_financial_reports(symbol):
    try:
        file_path = os.path.join(OUTPUT_DIR, f"{symbol.upper()}.json")
        
        if os.path.exists(file_path):
            os.remove(file_path)

        fun = Fundamental()
        stock_obj = fun.equity(symbol)
        
        df_balance = stock_obj.balance_sheet(period='quarter')
        df_income = stock_obj.income_statement(period='quarter')
        
        df_cashflow = None
        try:
            df_cashflow = stock_obj.cash_flow(period='quarter')
        except Exception as e:
            print(f"⚠️ Không lấy được bảng Cash Flow cho {symbol}: {e}")
            
        # BỔ SUNG: Cào thêm bảng Chỉ số tài chính & Định giá (P/E, P/B, P/S, ROE, ROA, Biên gộp...)
        df_ratio = None
        try:
            df_ratio = stock_obj.ratio(period='quarter')
        except Exception as e:
            print(f"⚠️ Không lấy được bảng Chỉ số tài chính (ratio) cho {symbol}: {e}")
        
        reports = {}
        if df_balance is not None and not df_balance.empty:
            reports['balance_sheet'] = df_balance.to_dict(orient="records")
        if df_income is not None and not df_income.empty:
            reports['income_statement'] = df_income.to_dict(orient="records")
        if df_cashflow is not None and not df_cashflow.empty:
            reports['cash_flow'] = df_cashflow.to_dict(orient="records")
        if df_ratio is not None and not df_ratio.empty:
            reports['ratios'] = df_ratio.to_dict(orient="records")
            
        if not reports:
            print(f"⚠️ Không có dữ liệu BCTC cho mã: {symbol}")
            return False

        reports['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Đã tải và làm mới BCTC đầy đủ (kèm Cash Flow & Ratios) cho mã: {symbol}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi mã {symbol}: {e}")
        return False

def auto_git_push_bctc():
    try:
        print("\n📤 Đang tự động đồng bộ thư mục 'bctc_data' lên GitHub...")
        
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        pull_result = subprocess.run(
            ["git", "pull", "origin", "main", "--rebase", "--autostash"], 
            capture_output=True, text=True
        )
        if pull_result.returncode != 0:
            print("⚠️ Có xung đột khi pull, hủy rebase để ưu tiên file dưới máy...")
            subprocess.run(["git", "rebase", "--abort"], check=False)

        subprocess.run(["git", "add", "bctc_data/"], check=True)
        
        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("ℹ️ Không có dữ liệu BCTC mới nào thay đổi để đẩy lên.")
            return

        commit_msg = f"Auto update full BCTC data (with Cash Flow & Ratios) - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy dữ liệu BCTC lên GitHub thành công!")
        
    except Exception as e:
        print(f"⚠️ Lỗi Git push BCTC: {e}")

def main():
    print("==================================================")
    print("   CÀO ĐẦY ĐỦ BÁO CÁO TÀI CHÍNH & CHỈ SỐ TÀI CHÍNH")
    print("==================================================")
    
    # Lấy danh sách mã từ file JSON
    vn100_symbols = get_symbols_from_json()
    if not vn100_symbols:
        print("❌ Không tìm thấy danh sách mã nào. Vui lòng chạy script lấy danh sách VN100 trước.")
        return

    print(f"📋 Đã tải danh sách {len(vn100_symbols)} mã từ file JSON.")
    print("1. Cào TOÀN BỘ danh sách này")
    print("2. Cào MỘT NHÓM MÃ hoặc MÃ LẺ (Tùy chọn)")
    
    mode_choice = input("Nhập lựa chọn của bạn (1/2, mặc định 2): ").strip()
    
    target_symbols = []
    if mode_choice == '1':
        target_symbols = vn100_symbols
        print("-> Đã chọn chế độ cào toàn bộ danh sách.")
    else:
        raw_input_symbols = input("Nhập mã cần cào (cách nhau bởi dấu phẩy, VD: FPT,MWG,HPG): ").strip()
        if raw_input_symbols:
            target_symbols = [s.strip().upper() for s in raw_input_symbols.split(",") if s.strip()]
            print(f"-> Đã chọn cào các mã: {target_symbols}")
        else:
            target_symbols = ["FPT"]
            print("⚠️ Không nhận được mã hợp lệ, mặc định cào mã: FPT")

    total = len(target_symbols)
    print(f"\n🚀 Bắt đầu lấy dữ liệu BCTC & Ratios qua vnstock cho {total} mã...")
    
    successful_symbols = []
    for i, symbol in enumerate(target_symbols):
        print(f"[{i+1}/{total}] Xử lý: {symbol}...")
        if fetch_financial_reports(symbol):
            successful_symbols.append(symbol)
        time.sleep(0.5) 
        
    print(f"\n🎉 Hoàn tất! Đã làm mới thành công {len(successful_symbols)}/{total} file BCTC.")
    
    if successful_symbols:
        auto_git_push_bctc()

if __name__ == "__main__":
    main()
