import os
import json
import time
import subprocess
import datetime
from vnstock3 import Vnstock

OUTPUT_DIR = "bctc_data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

VN100_SYMBOLS = [
    "ACB", "BID", "CTG", "TCB", "MBB", "STB", "VPB", "HDB", "VIB", "TPB",
    "SHB", "SSB", "LPB", "MSB", "OCB", "EIB", "SSI", "VCI", "HCM", "VIX",
    "MBS", "FTS", "BSI", "CTS", "ORS", "VHM", "VIC", "VRE", "NVL", "PDR",
    "DIG", "NLG", "KDH", "CEO", "DXG", "TCH", "HDG", "KBC", "IDC", "SZC",
    "BCM", "PHR", "HPG", "HSG", "NKG", "CTD", "VCG", "HHV", "FPT", "MWG",
    "PNJ", "FRT", "VNM", "MSN", "SAB", "GAS", "PVD", "PVS", "BSR", "POW",
    "REE", "PC1", "NT2", "GMD", "HAH", "PVT", "VJC", "HVN", "VHC", "ANV"
]

def fetch_financial_reports(symbol):
    try:
        # Khởi tạo đối tượng Vnstock với nguồn VCI hoặc TCBS
        stock = Vnstock(symbol=symbol, source='VCI')
        
        # Lấy Bảng cân đối kế toán và Kết quả kinh doanh theo quý
        df_balance = stock.finance.balance_sheet(period='quarter', lang='vi')
        df_income = stock.finance.income_statement(period='quarter', lang='vi')
        
        reports = {}
        if df_balance is not None and not df_balance.empty:
            reports['balance_sheet'] = df_balance.to_dict(orient="records")
        if df_income is not None and not df_income.empty:
            reports['income_statement'] = df_income.to_dict(orient="records")
            
        if not reports:
            print(f"⚠️ Không có dữ liệu BCTC cho mã: {symbol}")
            return False

        file_path = os.path.join(OUTPUT_DIR, f"{symbol}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Đã tải xong BCTC cho mã: {symbol}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi mã {symbol}: {e}")
        return False

def auto_git_push_bctc():
    try:
        print("\n📤 Đang đồng bộ thư mục 'bctc_data' lên GitHub...")
        subprocess.run(["git", "add", OUTPUT_DIR], check=True)
        commit_msg = f"Auto update BCTC data via vnstock3 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Đẩy dữ liệu BCTC lên GitHub thành công!")
    except Exception as e:
        print(f"ℹ️ Git push info: {e}")

def main():
    total = len(VN100_SYMBOLS)
    print(f"🚀 Bắt đầu lấy dữ liệu BCTC qua vnstock3 cho {total} mã...")
    
    success = 0
    for i, symbol in enumerate(VN100_SYMBOLS):
        print(f"[{i+1}/{total}] Xử lý: {symbol}...")
        if fetch_financial_reports(symbol):
            success += 1
        time.sleep(0.4)
        
    print(f"\n🎉 Hoàn tất! Đã lưu thành công {success}/{total} file BCTC.")
    auto_git_push_bctc()

if __name__ == "__main__":
    main()
