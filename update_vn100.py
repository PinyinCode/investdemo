import json
import os
import time
import requests

SYMBOLS_FILE = "symbols.json"

# Danh sách công ty dự phòng nếu API VNDirect thiếu
FALLBACK_NAMES = {
    "ACB": "Ngân hàng TMCP Á Châu",
    "BCM": "Tổng Công ty Đầu tư và Phát triển Công nghiệp - CTCP",
    "BID": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
    "CTG": "Ngân hàng TMCP Công Thương Việt Nam",
    "FPT": "Công ty Cổ phần FPT",
    "HPG": "Công ty Cổ phần Tập đoàn Hòa Phát",
    "VNM": "Công ty Cổ phần Sữa Việt Nam",
    "VHM": "Công ty Cổ phần Vinhomes",
    "VIC": "Tập đoàn Vingroup - Công ty Cổ phần",
    "VCB": "Ngân hàng TMCP Ngoại thương Việt Nam"
    # Bạn có thể copy toàn bộ dict COMPANY_NAMES từ code cũ của bạn vào đây
}

def fetch_vn100_symbols():
    """Lấy danh sách mã VN100 từ VPS"""
    try:
        url = "https://bgapidatafeed.vps.com.vn/getlistindexsymbol?index=VN100"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return [item.get("symbol") for item in data if item.get("symbol")]
            elif isinstance(data, dict) and "symbols" in data:
                return data["symbols"]
    except Exception as e:
        print(f"❌ Lỗi lấy rổ VN100 từ VPS: {e}")
    return []

def get_vndirect_ratio(symbol, ratio_code):
    """Lấy chỉ số từ VNDirect (Vốn hóa, Số lượng CP)"""
    url = "https://api-finfo.vndirect.com.vn/v4/ratios"
    params = {"q": f"code:{symbol}~ratioCode:{ratio_code}", "size": 1, "sort": "reportDate:desc"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                return float(data[0].get("value", 0) or 0)
    except Exception:
        pass
    return 0.0

def get_company_info(symbol):
    """Lấy thông tin chi tiết: Tên, Vốn hóa, Số lượng CP"""
    # 1. Tên công ty (Lấy từ VNDirect, nếu không có thì dùng Fallback)
    company_name = FALLBACK_NAMES.get(symbol, symbol)
    try:
        url = "https://api-finfo.vndirect.com.vn/v4/company_info"
        r = requests.get(url, params={"q": f"code:{symbol}"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data and data[0].get("companyName"):
                company_name = data[0].get("companyName")
    except Exception:
        pass

    # 2. Vốn hóa (MARKET_CAP) - Đơn vị VND
    market_cap = get_vndirect_ratio(symbol, "MARKET_CAP")
    
    # 3. Số lượng cổ phiếu (SHARE_OUTSTANDING)
    total_shares = get_vndirect_ratio(symbol, "SHARE_OUTSTANDING")

    # Nếu API trả về vốn hóa bằng 0, tính bù bằng Giá * Số lượng CP (nếu có giá)
    # (Nhưng ở bước này ta chưa có giá, nên để 0 và cập nhật sau)
    
    return {
        "symbol": symbol,
        "company_name": company_name,
        "market_cap": int(market_cap) if market_cap else 0,
        "total_shares": int(total_shares) if total_shares else 0
    }

def main():
    print("🔄 Đang lấy danh sách VN100 từ VPS...", flush=True)
    symbols = fetch_vn100_symbols()
    
    if not symbols:
        print("❌ Không lấy được danh sách VN100. Dừng script.", flush=True)
        return

    symbols = sorted(list(set(symbols)))
    print(f"✅ Tìm thấy {len(symbols)} mã. Đang lấy thông tin chi tiết...", flush=True)

    result = []
    total = len(symbols)

    for i, sym in enumerate(symbols, 1):
        print(f"[{i:>3}/{total}] Đang lấy {sym:<6} ...", end="", flush=True)
        info = get_company_info(sym)
        result.append(info)
        print(f" ✅ {info['company_name'][:30]}... (Vốn hóa: {info['market_cap']:,})", flush=True)
        time.sleep(0.2)  # Tránh spam API VNDirect

    # Lưu ra file JSON
    with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"\n🎉 Đã lưu {len(result)} mã vào {SYMBOLS_FILE}", flush=True)

if __name__ == "__main__":
    main()
