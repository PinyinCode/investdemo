import json
import time
import os
import sys
import concurrent.futures
from vnstock import Company, Quote, Listing
from lotusmarket import fetchers

SYMBOLS_FILE = "vn100_symbols.json"
OUTPUT_FILE = "vn100_full_info.json"

def fetch_vn100_list():
    """Lấy danh sách VN100 bằng vnstock (Không dùng API VPS để tránh lỗi)"""
    print("🔄 Đang lấy danh sách mã VN100 từ VCI (vnstock)...", flush=True)
    
    # Thử dùng vnstock lấy danh sách
    try:
        listing = Listing(source='VCI')
        df = listing.symbols_by_group('VN100')
        
        if df is not None and not df.empty:
            col_name = 'symbol' if 'symbol' in df.columns else 'ticker'
            symbols = df[col_name].astype(str).tolist()
            symbols = sorted(list(set(symbols)))
            
            if symbols:
                with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
                    json.dump(symbols, f, ensure_ascii=False, indent=4)
                print(f"✅ Đã lấy và lưu {len(symbols)} mã vào {SYMBOLS_FILE}", flush=True)
                return symbols
    except Exception as e:
        print(f"⚠️ Lỗi khi dùng vnstock lấy rổ VN100: {e}", flush=True)
    
    # Nếu API lỗi, đọc file cũ
    print("⚠️ Thử đọc danh sách từ file cũ...", flush=True)
    if os.path.exists(SYMBOLS_FILE):
        try:
            with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    print("❌ Không có danh sách mã. Dừng script.", flush=True)
    return []

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

def get_price_with_timeout(symbol, timeout=5):
    def fetch_lotus():
        try:
            stock = fetchers.vps(symbol)
            return getattr(stock, "close", 0)
        except Exception:
            return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fetch_lotus)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return 0
        except Exception:
            return 0

def get_company_info(symbol, old_data):
    company_name = symbol
    total_shares = 0
    market_cap = 0
    close_price = 0

    try:
        comp = Company(symbol=symbol, source='VCI')
        overview = comp.overview()
        if overview is not None and not overview.empty:
            row = overview.iloc[0]
            company_name = str(row.get('organ_name', symbol))
            if 'issue_share' in row and row['issue_share']:
                total_shares = int(float(row['issue_share']))
            elif 'outstanding_share' in row and row['outstanding_share']:
                total_shares = int(float(row['outstanding_share']))
    except Exception:
        pass

    close_price = get_price_with_timeout(symbol, timeout=5)

    if close_price == 0:
        try:
            quote = Quote(source='VCI', symbol=symbol)
            df = quote.history(start="2026-10-01", end="2026-11-08") 
            if df is not None and not df.empty:
                close_price = float(df.iloc[-1]['close'])
                if close_price < 1000:
                    close_price = close_price * 1000
        except Exception:
            pass

    if close_price == 0 and symbol in old_data:
        close_price = old_data[symbol].get("close_price", 0)

    if close_price > 0 and total_shares > 0:
        market_cap = int(close_price * total_shares)

    return {
        "symbol": symbol,
        "company_name": company_name,
        "market_cap": market_cap,
        "total_shares": total_shares,
        "close_price": int(close_price)
    }

def main():
    # Bước 1: Lấy danh sách VN100
    all_symbols = fetch_vn100_list()
    if not all_symbols:
        return

    # Bước 2: Kiểm tra tham số chia phần
    part = 0
    if len(sys.argv) > 1:
        try:
            part = int(sys.argv[1])
        except ValueError:
            pass

    if part > 0:
        total_symbols = len(all_symbols)
        chunk_size = (total_symbols + 3) // 4 
        start_idx = (part - 1) * chunk_size
        end_idx = min(part * chunk_size, total_symbols)
        symbols_to_crawl = all_symbols[start_idx:end_idx]
        
        print("=" * 60, flush=True)
        print(f"🚀 CHẠY PHẦN {part}/4 — Gồm {len(symbols_to_crawl)} mã (Từ {start_idx+1} đến {end_idx})", flush=True)
        print("=" * 60, flush=True)
    else:
        symbols_to_crawl = all_symbols
        print(f"🚀 CHẠY TOÀN BỘ {len(symbols_to_crawl)} mã", flush=True)

    old_data = get_old_data()
    result = []
    
    for item in old_data.values():
        if item["symbol"] not in symbols_to_crawl:
            result.append(item)

    for i, sym in enumerate(symbols_to_crawl, 1):
        print(f"[{i:>2}/{len(symbols_to_crawl)}] Đang lấy {sym:<6} ...", end="", flush=True)
        
        try:
            info = get_company_info(sym, old_data)
            result.append(info)
            
            name_short = (info['company_name'][:22] + '...') if len(info['company_name']) > 22 else info['company_name']
            cap_billion = info['market_cap'] / 1_000_000_000
            warning = " ⚠️" if info['close_price'] == 0 else ""
            
            print(f" ✅ {name_short:<25} | Giá: {info['close_price']:>7,} | Vốn hóa: {cap_billion:>8,.0f} tỷ{warning}", flush=True)
        except Exception as e:
            print(f" ❌ Lỗi: {e}", flush=True)
            result.append({"symbol": sym, "company_name": sym, "market_cap": 0, "total_shares": 0, "close_price": 0})

        time.sleep(1.5) 

    result = sorted(result, key=lambda x: x["symbol"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 HOÀN TẤT! Đã lưu vào file: {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()