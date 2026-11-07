import json
import os
import subprocess
import datetime
from vnstock import Listing

SYMBOLS_FILE = "vn100_symbols.json"

def get_vn100_symbols():
    print("🔄 Đang lấy danh sách mã VN100...", flush=True)
    symbols = []
    
    # Cách 1: Thử lấy trực tiếp VN100 từ TCBS hoặc SSI (thường đầy đủ 100 mã hơn VCI)
    for source in ['TCBS', 'SSI', 'VCI']:
        try:
            print(f"👉 Thử lấy rổ VN100 từ nguồn: {source}...")
            listing = Listing(source=source)
            data = listing.symbols_by_group('VN100')
            if data is not None and len(data) > 80: # Kiểm tra nếu trả về số lượng hợp lý (>80 mã)
                col = 'symbol' if 'symbol' in data.columns else data.columns[0]
                symbols = data[col].dropna().astype(str).str.strip().tolist()
                print(f"✅ Lấy thành công {len(symbols)} mã từ {source}")
                break
        except Exception as e:
            print(f"⚠️ Nguồn {source} lỗi: {e}")
            
    # Cách 2: Nếu các nguồn trên đều thiếu (ví dụ chỉ trả về 77 mã), tiến hành gộp VN30 + VNMidCap
    if len(symbols) < 90:
        print("⚠️ Danh sách VN100 bị thiếu, tiến hành gộp nhóm VN30 và VNMidCap...")
        try:
            listing = Listing(source='VCI') # Hoặc TCBS
            vn30 = listing.symbols_by_group('VN30')
            vn_mid = listing.symbols_by_group('VNMidCap')
            
            combined = []
            for df in [vn30, vn_mid]:
                if df is not None:
                    col = 'symbol' if 'symbol' in df.columns else df.columns[0]
                    combined.extend(df[col].dropna().astype(str).str.strip().tolist())
            
            if combined:
                symbols = combined
                print(f"✅ Gộp thành công tổng số {len(symbols)} mã từ VN30 + VNMidCap.")
        except Exception as e:
            print(f"❌ Lỗi khi gộp nhóm: {e}")

    # Chuẩn hóa danh sách cuối cùng
    symbols = sorted(list(set([s.upper() for s in symbols if s and len(s) <= 5])))
    
    if symbols:
        with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
            json.dump(symbols, f, ensure_ascii=False, indent=4)
        print(f"💾 Đã lưu tổng cộng {len(symbols)} mã vào {SYMBOLS_FILE}")
        return symbols
        
    return []

def auto_git_push_symbols():
    """Tự động đẩy file symbols lên GitHub"""
    try:
        print(f"\n📤 Đang tự động đồng bộ file {SYMBOLS_FILE} lên GitHub...")
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        pull_result = subprocess.run(
            ["git", "pull", "origin", "main", "--rebase", "--autostash"], 
            capture_output=True, text=True
        )
        if pull_result.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], check=False)

        subprocess.run(["git", "add", SYMBOLS_FILE], check=True)
        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("ℹ️ Không có thay đổi nào để đẩy lên.")
            return

        commit_msg = f"Auto update {SYMBOLS_FILE} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy danh sách lên GitHub thành công!")
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

if __name__ == "__main__":
    syms = get_vn100_symbols()
    if syms:
        auto_git_push_symbols()
