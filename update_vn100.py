import json
import os
import time
import requests
from lotusmarket import fetchers

SYMBOLS_FILE = "symbols.json"

# Danh sách dự phòng nếu API VPS chặn IP
FALLBACK_VN100 = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
    "VCI", "HCM", "VIX", "MBS", "FTS", "BSI", "CTS", "ORS", "NVL", "PDR",
    "DIG", "NLG", "KDH", "CEO", "DXG", "TCH", "HDG", "KBC", "IDC", "SZC",
    "PHR", "HSG", "NKG", "CTD", "VCG", "HHV", "PNJ", "FRT", "PVD", "PVS",
    "BSR", "REE", "PC1", "NT2", "GMD", "HAH", "PVT", "HVN", "VHC", "ANV",
    "APH", "ASM", "DBC", "DCM", "DPM", "GEX", "KDC", "LIG", "MSH", "PAN",
    "SBT", "TCD", "TLG", "VDP", "VPG", "VTO", "DHC", "IMP", "SBA", "SJS",
    "TID", "VPI", "DRC", "CSM", "BMP", "NTC", "DHG", "VOS", "HAG"
]

def fetch_vn100_symbols():
    """Cố gắng lấy danh sách VN100 từ VPS với Header giả lập trình duyệt"""
    try:
        url = "https://bgapidatafeed.vps.com.vn/getlistindexsymbol?index=VN100"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://vps.com.vn",
            "Referer": "https://vps.com.vn/"
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return [item.get("symbol") for item in data if item.get("symbol")]
            elif isinstance(data, dict) and "symbols" in data:
                return data["symbols"]
    except Exception as e:
        print(f"⚠️ Lỗi lấy rổ VN100 từ VPS: {e}", flush=True)
    
    print("⚠️ Chuyển sang dùng danh sách VN100 tĩnh (Fallback).", flush=True)
    return FALLBACK_VN100

def get_company_info(symbol):
    """Lấy thông tin cơ bản dùng lotusmarket (KBS)"""
    company_name = symbol
    market_cap = 0
    total_shares = 0
    
    try:
        # Gọi KBS lấy dữ liệu cơ bản (tên, vốn hóa, số lượng cp)
        stock = fetchers.kbs(symbol)
        if stock:
            company_name = getattr(stock, "company_name", symbol) or symbol
            # Một số trường có thể có tên khác nhau tùy version lotusmarket
            market_cap = getattr(stock, "market_cap", 0) or 0
            total_shares = getattr(stock, "total_shares", 0) or getattr(stock, "shares_outstanding", 0) or 0
    except Exception as e:
        print(f"⚠️ Lỗi KBS {symbol}: {e}", flush=True)

    return {
        "symbol": symbol,
        "company_name": company_name,
        "market_cap": int(market_cap) if market_cap else 0,
        "total_shares": int(total_shares) if total_shares else 0,
    }

def main():
    print("🔄 Đang lấy danh sách VN100...", flush=True)
    symbols = fetch_vn100_symbols()

    if not symbols:
        print("❌ Không có mã nào để xử lý. Dừng script.", flush=True)
        return

    symbols = sorted(list(set(symbols)))
    print(f"✅ Tìm thấy {len(symbols)} mã. Đang lấy thông tin chi tiết qua lotusmarket...", flush=True)

    result = []
    total = len(symbols)

    for i, sym in enumerate(symbols, 1):
        print(f"[{i:>3}/{total}] Đang lấy {sym:<6} ...", end="", flush=True)
        info = get_company_info(sym)
        result.append(info)
        
        # In log gọn gàng
        name_short = info['company_name'][:25] if info['company_name'] else "N/A"
        print(f" ✅ {name_short}... (Vốn hóa: {info['market_cap']:,})", flush=True)
        
        time.sleep(0.2)

    with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 Đã lưu {len(result)} mã vào {SYMBOLS_FILE}", flush=True)

if __name__ == "__main__":
    main()
