import os
import datetime
import time
import json
import subprocess
import numpy as np
import requests
from vnstock import Quote

DATA_FILE = "data.json"
HISTORY_DIR = "history"
BCTC_DIR = "bctc_data"
JS_LIB_FILE = "lightweight-charts.js"

VN100_SYMBOLS = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
    "VCI", "HCM", "VIX", "MBS", "FTS", "BSI", "CTS", "ORS", "NVL", "PDR",
    "DIG", "NLG", "KDH", "CEO", "DXG", "TCH", "HDG", "KBC", "IDC", "SZC",
    "PHR", "HSG", "NKG", "CTD", "VCG", "HHV", "PNJ", "FRT", "PVD", "PVS",
    "BSR", "REE", "PC1", "NT2", "GMD", "HAH", "PVT", "HVN", "VHC", "ANV",
    "APH", "ASM", "DBC", "DCM", "DPM", "GEX", "KDC", "LIG", "MSH", "PAN",
    "SBT", "TCD", "TLG", "VDP", "VPG", "VTO", "DHC", "IMP", "SBA", "SJS",
    "TID", "VPI", "DRC", "CSM", "BMP", "NTC", "DHG", "VHC", "VOS", "HAG"
]

# Đảm bảo danh sách luôn chuẩn 100 mã độc nhất
VN100_SYMBOLS = sorted(list(set(VN100_SYMBOLS)))

VNDIRECT_RATIOS = {
    "pe": "PRICE_TO_EARNINGS",
    "pb": "PRICE_TO_BOOK",
    "eps": "EPS_TR",
    "roe": "ROAE_TR_AVG5Q",
    "roa": "ROAA_TR_AVG5Q",
    "dividend_yield": "DIVIDEND_YIELD"
}

def get_vndirect_ratio(symbol, ratio_code):
    url = "https://api-finfo.vndirect.com.vn/v4/ratios"
    params = {"q": f"code:{symbol}~ratioCode:{ratio_code}", "size": 1, "sort": "reportDate:desc"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                return float(data[0].get("value", 0))
    except Exception:
        pass
    return 0

def aggregate_candles(data, interval):
    """Thuật toán gom nhóm nến D1 thành W1 (Tuần) hoặc MN (Tháng) chuẩn xác"""
    if not data:
        return []
    if interval == 'D1':
        return data

    groups = {}
    for bar in data:
        date = datetime.datetime.strptime(bar['time'], '%Y-%m-%d')
        if interval == 'W1':
            start_of_week = date - datetime.timedelta(days=date.weekday())
            key = start_of_week.strftime('%Y-%m-%d')
        elif interval == 'MN':
            key = date.strftime('%Y-%m-01')

        if key not in groups:
            groups[key] = {
                "time": key,
                "open": bar['open'],
                "high": bar['high'],
                "low": bar['low'],
                "close": bar['close'],
                "volume": bar['volume']
            }
        else:
            groups[key]['high'] = max(groups[key]['high'], bar['high'])
            groups[key]['low'] = min(groups[key]['low'], bar['low'])
            groups[key]['close'] = bar['close']
            groups[key]['volume'] += bar['volume']

    return sorted(list(groups.values()), key=lambda x: x['time'])

def fetch_history_with_fallback(symbol, start_date, end_date):
    """Thử lần lượt các nguồn TCBS và VCI với cơ chế đổi User-Agent phòng chống chặn"""
    sources = ['TCBS', 'VCI']
    for src in sources:
        for attempt in range(2):
            try:
                quote = Quote(source=src, symbol=symbol)
                df = quote.history(start=start_date, end=end_date)
                if df is not None and not df.empty:
                    return df
            except Exception:
                time.sleep(1)
        time.sleep(0.5)
    return None

def parse_bctc_history(symbol):
    """Đọc file BCTC JSON chi tiết (hỗ trợ 8 quý) trong thư mục bctc_data, 
    tính toán các chỉ số tăng trưởng QoQ, YoY và chuỗi thời gian chi tiết."""
    filepath = os.path.join(BCTC_DIR, f"{symbol}.json")
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    balance_sheet = data.get("balance_sheet", [])
    income_statement = data.get("income_statement", [])
    if not balance_sheet or not income_statement:
        return []

    bs_dict = {}
    for item in balance_sheet:
        p = item.get("period")
        if p not in bs_dict:
            bs_dict[p] = {}
        bs_dict[p][item.get("id")] = item.get("value")

    is_dict = {}
    for item in income_statement:
        p = item.get("period")
        if p not in is_dict:
            is_dict[p] = {}
        is_dict[p][item.get("id")] = item.get("value")

    periods = sorted(list(set(bs_dict.keys()).intersection(set(is_dict.keys()))), reverse=True)
    if not periods:
        return []

    bctc_records = []
    for idx, curr_p in enumerate(periods):
        prev_p = periods[idx + 1] if idx + 1 < len(periods) else None
        year, q_str = curr_p.split("-")
        yoy_p = f"{int(year) - 1}-{q_str}"

        # Lấy số liệu linh hoạt (hỗ trợ cả ngân hàng lẫn phi ngân hàng)
        total_assets = bs_dict[curr_p].get("BS_TOTAL_ASSETS", bs_dict[curr_p].get("TOTAL_ASSETS", 0))
        loans = bs_dict[curr_p].get("BS_LOANS_TO_CUSTOMERS", 0) # Riêng ngân hàng
        equity = bs_dict[curr_p].get("BS_EQUITY", bs_dict[curr_p].get("EQUITY", 0))
        
        nii = is_dict[curr_p].get("IS_NET_INTEREST_INCOME", 0) # Ngân hàng
        pat = is_dict[curr_p].get("IS_NET_PROFIT_AFTER_TAX", is_dict[curr_p].get("NET_PROFIT_AFTER_TAX", 0))

        # Tăng trưởng QoQ & YoY cho khoản vay (hoặc tài sản)
        loans_prev = bs_dict.get(prev_p, {}).get("BS_LOANS_TO_CUSTOMERS", 0) if prev_p else 0
        loans_yoy = bs_dict.get(yoy_p, {}).get("BS_LOANS_TO_CUSTOMERS", 0)
        credit_growth_qoq = ((loans - loans_prev) / loans_prev * 100) if loans_prev else 0
        credit_growth_yoy = ((loans - loans_yoy) / loans_yoy * 100) if loans_yoy else 0

        pat_prev = is_dict.get(prev_p, {}).get("IS_NET_PROFIT_AFTER_TAX", is_dict.get(prev_p, {}).get("NET_PROFIT_AFTER_TAX", 0)) if prev_p else 0
        pat_yoy = is_dict.get(yoy_p, {}).get("IS_NET_PROFIT_AFTER_TAX", is_dict.get(yoy_p, {}).get("NET_PROFIT_AFTER_TAX", 0))
        pat_growth_qoq = ((pat - pat_prev) / pat_prev * 100) if pat_prev else 0
        pat_growth_yoy = ((pat - pat_yoy) / pat_yoy * 100) if pat_yoy else 0

        roe_q = (pat / equity * 100) if equity else 0

        bctc_records.append({
            "period": curr_p,
            "total_assets": round(total_assets / 1e9, 2),
            "loans": round(loans / 1e9, 2),
            "equity": round(equity / 1e9, 2),
            "net_interest_income": round(nii / 1e9, 2),
            "net_profit": round(pat / 1e9, 2),
            "credit_growth_qoq": round(credit_growth_qoq, 2),
            "credit_growth_yoy": round(credit_growth_yoy, 2),
            "profit_growth_qoq": round(pat_growth_qoq, 2),
            "profit_growth_yoy": round(pat_growth_yoy, 2),
            "roe_quarter": round(roe_q, 2)
        })

    return bctc_records

def extract_advanced_metrics_from_bctc(symbol):
    """Trích xuất các thông số chuyên sâu (CFO, D/E, Gross Margin, TTM Net Profit) từ chuỗi 8 quý gần nhất"""
    filepath = os.path.join(BCTC_DIR, f"{symbol}.json")
    if not os.path.exists(filepath):
        return {"cfo_latest": 0, "debt_to_equity": 0, "gross_margin": 0, "net_profit_ttm": 0}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"cfo_latest": 0, "debt_to_equity": 0, "gross_margin": 0, "net_profit_ttm": 0}

    balance_sheet = data.get("balance_sheet", [])
    cash_flow = data.get("cash_flow", [])
    income_statement = data.get("income_statement", [])

    latest_period = balance_sheet[0].get("period") if balance_sheet else None

    # Lấy CFO kỳ gần nhất
    latest_cfo = 0
    if cash_flow and latest_period:
        for item in cash_flow:
            if item.get("period") == latest_period and item.get("id") in ["CF_OPERATE_CASH_FLOW", "CFO"]:
                latest_cfo = item.get("value", 0)
                break
        if latest_cfo == 0 and cash_flow:
            latest_cfo = cash_flow[0].get("value", 0)

    # Đòn bẩy D/E kỳ gần nhất
    total_liabilities = 0
    equity = 0
    if balance_sheet and latest_period:
        for item in balance_sheet:
            if item.get("period") == latest_period:
                if item.get("id") in ["BS_TOTAL_LIABILITIES", "TOTAL_LIABILITIES"]:
                    total_liabilities = item.get("value", 0)
                elif item.get("id") in ["BS_EQUITY", "EQUITY"]:
                    equity = item.get("value", 0)
    debt_to_equity = round(total_liabilities / equity, 2) if equity > 0 else 0

    # Biên lợi nhuận gộp kỳ gần nhất
    gross_profit = 0
    revenue = 0
    if income_statement and latest_period:
        for item in income_statement:
            if item.get("period") == latest_period:
                if item.get("id") in ["IS_GROSS_PROFIT", "GROSS_PROFIT"]:
                    gross_profit = item.get("value", 0)
                elif item.get("id") in ["IS_NET_REVENUE", "REVENUE", "NET_REVENUE"]:
                    revenue = item.get("value", 0)
    gross_margin = round((gross_profit / revenue) * 100, 1) if revenue > 0 else 0

    # Tính TTM (Trailing Twelve Months - Tổng lợi nhuận 4 quý gần nhất)
    net_profit_ttm = 0
    if income_statement:
        pat_items = [item for item in income_statement if item.get("id") in ["IS_NET_PROFIT_AFTER_TAX", "NET_PROFIT_AFTER_TAX"]]
        pat_items = sorted(pat_items, key=lambda x: x.get("period", ""), reverse=True)
        latest_4q = pat_items[:4]
        net_profit_ttm = sum([q.get("value", 0) for q in latest_4q])

    return {
        "cfo_latest": round(latest_cfo / 1e9, 2),
        "debt_to_equity": debt_to_equity,
        "gross_margin": gross_margin,
        "net_profit_ttm": round(net_profit_ttm / 1e9, 2)
    }

def auto_git_push():
    """Tự động đồng bộ dữ liệu lên GitHub an toàn, tránh lỗi rejected"""
    try:
        print("📤 Đang tiến hành đồng bộ dữ liệu lên GitHub...")
        subprocess.run(["git", "add", DATA_FILE], check=True)
        subprocess.run(["git", "add", HISTORY_DIR], check=True)
        if os.path.exists("bctc_data"):
            subprocess.run(["git", "add", "bctc_data"], check=True)
        if os.path.exists(JS_LIB_FILE):
            subprocess.run(["git", "add", JS_LIB_FILE], check=True)
            
        commit_msg = f"Auto update symbols data & BCTC (8 quarters) - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        subprocess.run(["git", "pull", "origin", "main", "--rebase"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy dữ liệu lên GitHub thành công!")
    except subprocess.CalledProcessError:
        print("⚠️ Git: Đã cố gắng đồng bộ nhưng có thể cần kiểm tra xung đột thủ công nếu có.")
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

def main():
    print("==================================================")
    print("        BƯỚC 1: CHỌN PHẠM VI MÃ CỔ PHIẾU        ")
    print("==================================================")
    print("1. Cào TOÀN BỘ danh sách VN100 (Mặc định)")
    print("2. Cào RIÊNG TỪNG MÃ (Tùy chọn mã cụ thể)")
    
    target_symbols = VN100_SYMBOLS
    mode_choice = input("Nhập lựa chọn chế độ (1/2, mặc định 1): ").strip()
    if mode_choice == '2':
        raw_input_symbols = input("Nhập mã cổ phiếu muốn cào (cách nhau bởi dấu phẩy, VD: PNJ,BID,ACB): ").strip()
        if raw_input_symbols:
            target_symbols = [s.strip().upper() for s in raw_input_symbols.split(",") if s.strip()]
            print(f"-> Đã chọn cào riêng các mã: {target_symbols}")
        else:
            print("⚠️ Không nhận được mã hợp lệ, tự động quay về cào toàn bộ VN100.")
    else:
        print("-> Đã chọn: Cào toàn bộ danh sách VN100.")

    print("\n==================================================")
    print("        BƯỚC 2: CHỌN SỐ PHIÊN GIAO DỊCH         ")
    print("==================================================")
    print("1. Gần nhất: 30 phiên giao dịch gần nhất (Mặc định)")
    print("2. Dài hạn: 10 năm gần đây (~2500 phiên)")
    print("3. Tùy chỉnh: Nhập số phiên tự do (VD: 2, 5, 100 phiên)")
    
    choice = input("Nhập lựa chọn số phiên (1/2/3, mặc định 1): ").strip()
    
    num_sessions = 30
    if choice == '2':
        num_sessions = 2500
        print("-> Đã chọn chế độ cào 10 năm dữ liệu (~2500 phiên).")
    elif choice == '3':
        try:
            custom_sessions = int(input("Nhập số phiên muốn cào (ví dụ: 2, 5, 100): ").strip())
            if custom_sessions > 0:
                num_sessions = custom_sessions
                print(f"-> Đã chọn cào tùy chỉnh: {num_sessions} phiên.")
        except ValueError:
            print("⚠️ Nhập sai định dạng, tự động quay về mặc định 30 phiên.")
    else:
        print("-> Đã chọn chế độ mặc định (30 phiên gần nhất).")

    print(f"\n🚀 Bắt đầu cào dữ liệu cho {len(target_symbols)} mã (Lấy đúng {num_sessions} phiên giao dịch gần nhất)...")
    
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

    stock_db = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                stock_db = json.load(f)
        except Exception:
            pass

    total = len(target_symbols)
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    approx_days = max(num_sessions * 2, 365)
    start_date = (datetime.datetime.now() - datetime.timedelta(days=approx_days)).strftime("%Y-%m-%d")

    for i, symbol in enumerate(target_symbols):
        print(f"[{i+1}/{total}] Đang xử lý: {symbol}...")
        closes, volumes = [], []
        close_price, volume = 0, 0
        history_d1 = []
        
        try:
            df = fetch_history_with_fallback(symbol, start_date, end_date)
            if df is not None and not df.empty:
                df = df.tail(num_sessions)
                
                closes = df['close'].tolist()
                volumes = df['volume'].tolist()
                close_price = closes[-1]
                volume = volumes[-1]
                
                new_history_d1 = []
                for _, row in df.iterrows():
                    time_val = row['time']
                    time_str = time_val.strftime('%Y-%m-%d') if hasattr(time_val, 'strftime') else str(time_val)[:10]
                    
                    new_history_d1.append({
                        "time": time_str,
                        "open": float(row.get('open', row['close'])),
                        "high": float(row.get('high', row['close'])),
                        "low": float(row.get('low', row['close'])),
                        "close": float(row['close']),
                        "volume": int(row.get('volume', 0))
                    })
                
                history_file_path = os.path.join(HISTORY_DIR, f"{symbol}.json")
                existing_history_d1 = []
                
                if os.path.exists(history_file_path):
                    try:
                        with open(history_file_path, "r", encoding="utf-8") as sf:
                            old_history_data = json.load(sf)
                            existing_history_d1 = old_history_data.get("history_d1", [])
                    except Exception:
                        pass
                
                merged_dict = {item['time']: item for item in existing_history_d1}
                for item in new_history_d1:
                    merged_dict[item['time']] = item
                
                history_d1 = sorted(list(merged_dict.values()), key=lambda x: x['time'])
                
                closes = [bar['close'] for bar in history_d1]
                volumes = [bar['volume'] for bar in history_d1]
                
        except Exception as e:
            print(f"⚠️ Lỗi xử lý lịch sử {symbol}: {e}")

        if close_price <= 0:
            print(f"⚠️ Bỏ qua {symbol} do không lấy được giá.")
            continue

        ratios = {}
        for key, code in VNDIRECT_RATIOS.items():
            ratios[key] = get_vndirect_ratio(symbol, code)
            time.sleep(0.2)

        status = "ĐANG TÍCH LŨY NỀN"
        detail = "Đang siết nền tích lũy biên độ hẹp."
        if len(closes) >= 20 and len(volumes) >= 20:
            recent_vols = volumes[-20:]
            ma_vol_20 = np.mean(recent_vols)
            vol_ratio = volume / ma_vol_20 if ma_vol_20 > 0 else 1.0
            price_change_pct = ((closes[-1] - closes[-2]) / closes[-2]) * 100 if closes[-2] > 0 else 0

            if vol_ratio < 0.7 and abs(price_change_pct) < 1.5:
                status = "ĐANG TÍCH LŨY NỀN (CẠN CUNG)"
                detail = f"Khối lượng cạn kiệt ở mức {vol_ratio:.2f}x MA20."
            elif vol_ratio > 1.5 and price_change_pct > 1.5:
                status = "SẴN SÀNG BREAKOUT (NỔ VOL)"
                detail = f"Khối lượng bùng nổ đạt {vol_ratio:.2f}x MA20 kèm giá tăng."
            elif closes[-1] > np.mean(closes[-20:]):
                status = "ĐANG GOM HÀNG"
                detail = "Dòng tiền duy trì ổn định trên MA20."

        history_w1 = aggregate_candles(history_d1, 'W1')
        history_mn = aggregate_candles(history_d1, 'MN')

        symbol_history_data = {
            "history_d1": history_d1,
            "history_w1": history_w1,
            "history_mn": history_mn
        }
        with open(os.path.join(HISTORY_DIR, f"{symbol}.json"), "w", encoding="utf-8") as sf:
            json.dump(symbol_history_data, sf, ensure_ascii=False)

        # Xử lý chuỗi 8 quý từ thư mục bctc_data
        bctc_history = parse_bctc_history(symbol)
        
        # Trích xuất các chỉ số nâng cao (CFO, D/E, Biên gộp, Lợi nhuận TTM 4 quý)
        adv_metrics = extract_advanced_metrics_from_bctc(symbol)
        
        old_data = stock_db.get(symbol, {})
        
        stock_db[symbol] = {
            "symbol": symbol,
            "close": int(close_price * 1000),
            "volume": int(volume),
            "pe": round(ratios.get("pe", 0), 2),
            "pb": round(ratios.get("pb", 0), 2),
            "eps": int(ratios.get("eps", 0)),
            "roe": round(ratios.get("roe", 0) * 100, 1),
            "roa": round(ratios.get("roa", 0) * 100, 1),
            "dividend_yield": round(ratios.get("dividend_yield", 0) * 100, 2),
            "cfo_latest": adv_metrics["cfo_latest"],          # Dòng tiền kinh doanh kỳ gần nhất (tỷ VNĐ)
            "debt_to_equity": adv_metrics["debt_to_equity"],  # Tỷ lệ D/E
            "gross_margin": adv_metrics["gross_margin"],      # Biên lợi nhuận gộp (%)
            "net_profit_ttm": adv_metrics["net_profit_ttm"],  # Lợi nhuận trượt 4 quý (TTM)
            "recommendation": status,
            "price_zone": detail,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bctc_history": bctc_history,                     # Toàn bộ lịch sử chuỗi 8 quý
            "outlook": old_data.get("outlook", ""),
            "ai_recommendation": old_data.get("ai_recommendation", ""),
            "ai_price_zone": old_data.get("ai_price_zone", ""),
            "macro_view": old_data.get("macro_view", ""),
            "ai_updated_at": old_data.get("ai_updated_at", "")
        }
        
        time.sleep(1.5)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
    print("✅ Đã hoàn tất cập nhật dữ liệu tài chính (chuỗi 8 quý & chỉ số nâng cao) vào data.json!")

    auto_git_push()

if __name__ == "__main__":
    main()
