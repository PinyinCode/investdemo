import json
import time
import os
import sys
import concurrent.futures
from vnstock import Company

OUTPUT_FILE = "vn100_full_info.json"

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

def main():
    if len(sys.argv) < 2:
        print("❌ Vui lòng nhập mã cổ phiếu. VD: python crawl_vn100_pc.py ACB")
        return

    symbol = sys.argv[1].upper().strip()
    
    print(f"🔄 Đang lấy dữ liệu cho mã: {symbol} ...", flush=True)
    
    company_name, close_price, total_shares, market_cap = get_company_info_with_timeout(symbol, timeout=10)

    if close_price == 0:
        print(f"❌ Không lấy được dữ liệu cho {symbol}. Có thể đang bị khóa IP hoặc mã không tồn tại.")
        return

    # Đọc dữ liệu cũ
    old_data = get_old_data()
    
    # Cập nhật thông tin mới
    old_data[symbol] = {
        "symbol": symbol,
        "company_name": company_name,
        "market_cap": market_cap,
        "total_shares": total_shares,
        "close_price": int(close_price)
    }

    # Chuyển dict thành list và sắp xếp A-Z
    result = sorted(list(old_data.values()), key=lambda x: x["symbol"])

    # Ghi đè lại file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    cap_billion = market_cap / 1_000_000_000
    shares_million = total_shares / 1_000_000
    
    print(f"✅ THÀNH CÔNG!")
    print(f"   - Tên công ty: {company_name}")
    print(f"   - Giá hiện tại: {close_price:,.0f} VNĐ")
    print(f"   - Số lượng CP: {shares_million:,.1f} triệu CP")
    print(f"   - Vốn hóa: {cap_billion:,.0f} tỷ VNĐ")
    print(f"📁 Đã lưu vào file: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
