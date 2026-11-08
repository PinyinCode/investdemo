import json
import os
import subprocess
import datetime
import pandas as pd
from vnstock import Listing

SYMBOLS_FILE = "vn100_symbols.json"

# Danh sách 100 mã VN100 chuẩn (Dự phòng nếu API bị thiếu)
# Bạn có thể cập nhật danh sách này hàng quý khi VN100 tái cơ cấu
VN100_FALLBACK = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
    "VHM", "BMP", "BSR", "DCM", "DGC", "DGW", "DHC", "DIG", "DXG", "FRT",
    "GMD", "HAH", "HDC", "HDG", "HHV", "HT1", "IMP", "KBC", "KDC", "KDH",
    "KOS", "NLG", "NT2", "NTL", "PDR", "PHR", "PNJ", "PPC", "PTB", "PVT",
    "REE", "SBT", "SCS", "SIP", "SJS", "SKG", "SSB", "SZC", "TCH", "TCM",
    "THG", "TLG", "TVB", "VCI", "VHC", "VND", "VPI", "VSC", "VSH", "AGG",
    "ANV", "APG", "ASM", "BCG", "BWE", "CII", "CTD", "CTI", "DBD", "DBC",
    "DCL", "DHC", "DPG", "EIB", "EVF", "FCN", "GEG", "GEX", "GIL", "HAG"
]

def get_vn100_symbols():
    print("🔄 Đang lấy danh sách mã VN100...", flush=True)
    symbols = []
    
    # Cách 1: Ưu tiên lấy từ KBS (Ổn định nhất) và VCI (Dự phòng)
    for source in ['kbs', 'vci']:
        try:
            print(f"👉 Thử lấy rổ VN100 từ nguồn: {source}...")
            listing = Listing(source=source)
            data = listing.symbols_by_group('VN100')
            
            # Xử lý linh hoạt cả trường hợp trả về Series hoặc DataFrame
            if data is not None and not data.empty:
                if isinstance(data, pd.Series):
                    df = data.to_frame(name='symbol')
                else:
                    df = data
                    
                col = 'symbol' if 'symbol' in df.columns else df.columns[0]
                temp_symbols = df[col].dropna().astype(str).str.strip().tolist()
                
                if len(temp_symbols) > 0:
                    symbols = temp_symbols
                    print(f"✅ Lấy thành công {len(symbols)} mã từ {source}")
                    break
        except Exception as e:
            print(f"⚠️ Nguồn {source} lỗi: {e}")

    # Cách 2: BÙ ĐẮP CÁC MÃ CÒN THIẾU TỪ DANH SÁCH DỰ PHÒNG
    if len(symbols) < 100:
        print(f"⚠️ API chỉ trả về {len(symbols)} mã. Tiến hành bù đắp từ danh sách dự phòng...")
        missing_count = 100 - len(symbols)
        
        # Duyệt qua danh sách dự phòng, nếu mã nào chưa có thì thêm vào
        for fb_sym in VN100_FALLBACK:
            if fb_sym not in symbols:
                symbols.append(fb_sym)
                missing_count -= 1
                if missing_count == 0:
                    break
                    
        print(f"✅ Đã bù đắp thành công. Tổng cộng: {len(symbols)} mã.")

    # Chuẩn hóa danh sách cuối cùng (Loại bỏ trùng lặp, viết hoa, cắt lấy đúng 100 mã)
    symbols = sorted(list(set([s.upper() for s in symbols if s and len(s) <= 5])))[:100]
    
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
