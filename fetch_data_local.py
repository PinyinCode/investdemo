import os
import datetime
import time
import json
import subprocess
import numpy as np
import requests
from vnstock import Quote

DATA_FILE = "data.json"
LAST_UPDATE_FILE = "last_update.json"
CHEAP_STOCKS_FILE = "cheap_stocks.json"  
HISTORY_DIR = "history"
BCTC_DIR = "bctc_data"
JS_LIB_FILE = "lightweight-charts.js"

VN100_INFO_FILE = "vn100_full_info.json"
VN100_SYMBOLS_FILE = "vn100_symbols.json"

# Hàm tự động dịch tên ngành từ VCI (tiếng Anh) sang key của Web (tiếng Việt)
def translate_sector(sector_name):
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

def load_vn100_data():
    """Tải danh sách mã, tên công ty và phân ngành động từ file JSON"""
    symbols = []
    company_names = {}
    sector_mapping = {}
    
    if os.path.exists(VN100_INFO_FILE):
        try:
            with open(VN100_INFO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    sym = item.get("symbol")
                    if sym:
                        symbols.append(sym)
                        company_names[sym] = item.get("company_name", sym)
                        
                        # Lấy ngành từ file JSON (nếu có) và tự động dịch
                        raw_sector = item.get("sector", "")
                        vn_sector = translate_sector(raw_sector)
                        
                        if vn_sector not in sector_mapping:
                            sector_mapping[vn_sector] = []
                        sector_mapping[vn_sector].append(sym)
            print(f"✅ Đã tải {len(symbols)} mã và phân ngành tự động từ {VN100_INFO_FILE}")
            return sorted(list(set(symbols))), company_names, sector_mapping
        except Exception as e:
            print(f"⚠️ Lỗi đọc {VN100_INFO_FILE}: {e}")

    # Fallback nếu chưa có file cào chi tiết
    if os.path.exists(VN100_SYMBOLS_FILE):
        try:
            with open(VN100_SYMBOLS_FILE, "r", encoding="utf-8") as f:
                symbols = json.load(f)
            company_names = {sym: sym for sym in symbols}
            print(f"⚠️ Không có file chi tiết, dùng {VN100_SYMBOLS_FILE} ({len(symbols)} mã)")
            return sorted(list(set(symbols))), company_names, {}
        except Exception as e:
            print(f"⚠️ Lỗi đọc {VN100_SYMBOLS_FILE}: {e}")

    print("❌ Không tìm thấy file danh sách mã nào! Vui lòng chạy script cào danh sách trước.")
    return [], {}, {}

# Tải dữ liệu động khi khởi động
VN100_SYMBOLS, COMPANY_NAMES, DYNAMIC_SECTOR_MAPPING = load_vn100_data()

# Bảng phân ngành dự phòng (Chỉ dùng nếu file JSON không có thông tin ngành)
FALLBACK_SECTOR_MAPPING = {
    "NGAN_HANG": ["ACB", "BID", "CTG", "TCB", "MBB", "STB", "VPB", "HDB", "VIB", "TPB", "SHB", "SSB", "MSB", "OCB", "EIB", "VCB"],
    "CHUNG_KHOAN": ["SSI", "VCI", "HCM", "VIX", "MBS", "FTS", "BSI", "CTS", "ORS"],
    "BAT_DONG_SAN": ["VHM", "VIC", "VRE", "NVL", "PDR", "DIG", "NLG", "KDH", "CEO", "DXG", "TCH", "HDG", "KBC", "IDC", "SZC", "BCM", "PHR", "SJS", "VPI"],
    "CONG_NGHE_BAN_LE": ["FPT", "MWG", "PNJ", "FRT"],
    "DIEN_NUOC_HA_TANG": ["POW", "REE", "PC1", "NT2", "GAS"],
    "NGUYEN_VAT_LIEU_CHU_KY": ["HPG", "HSG", "NKG", "DCM", "DPM", "GVR", "DHC", "BSR"],
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": ["SAB", "VNM", "MSN", "VHC", "ANV", "BVH", "PLX", "PVD", "PVS", "GMD", "HAH", "PVT", "HVN", "APH", "ASM", "DBC", "KDC", "MSH", "PAN", "SBT", "TCD", "TLG", "VDP", "VPG", "VTO", "IMP", "SBA", "DRC", "CSM", "BMP", "NTC", "DHG", "VOS", "HAG", "CTD", "VCG", "HHV", "GEX"]
}

# Gộp bảng động và bảng tĩnh (Ưu tiên bảng động)
SECTOR_MAPPING = {**FALLBACK_SECTOR_MAPPING, **DYNAMIC_SECTOR_MAPPING}

VNDIRECT_RATIOS = {
    "pe": "PRICE_TO_EARNINGS",
    "pb": "PRICE_TO_BOOK",
    "eps": "EPS_TR",
    "roe": "ROAE_TR_AVG5Q",
    "roa": "ROAA_TR_AVG5Q",
    "dividend_yield": "DIVIDEND_YIELD"
}


def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"


def get_vndirect_ratio(symbol, ratio_code):
    url = "https://api-finfo.vndirect.com.vn/v4/ratios"
    params = {"q": f"code:{symbol}~ratioCode:{ratio_code}", "size": 1, "sort": "reportDate:desc"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                val = data[0].get("value")
                if val is not None:
                    return float(val)
    except Exception:
        pass
    return None


def get_fallback_ratios_from_bctc(symbol):
    filepath = os.path.join(BCTC_DIR, f"{symbol.upper()}.json")
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        ratios_list = data.get("ratios", [])
        if ratios_list:
            latest = ratios_list[0]
            return {
                "pe": latest.get("PE") or latest.get("PRICE_TO_EARNINGS") or 0,
                "pb": latest.get("PB") or latest.get("PRICE_TO_BOOK") or 0,
                "ps": latest.get("PS") or latest.get("PRICE_TO_SALES") or 0,
                "eps": latest.get("EPS") or 0,
                "roe": latest.get("ROE") or 0,
                "roa": latest.get("ROA") or 0,
                "dividend_yield": latest.get("DIVIDEND_YIELD") or 0
            }
    except Exception:
        pass
    return {}


def get_company_overview(symbol, close_price=0):
    company_name = COMPANY_NAMES.get(symbol, symbol)
    total_shares = 0
    market_cap = 0

    try:
        url = "https://api-finfo.vndirect.com.vn/v4/ratios"
        params = {"q": f"code:{symbol}~ratioCode:SHARE_OUTSTANDING", "size": 1, "sort": "reportDate:desc"}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                total_shares = float(data[0].get("value", 0) or 0)
    except Exception:
        pass

    if total_shares == 0:
        try:
            url = "https://api-finfo.vndirect.com.vn/v4/ratios"
            params = {"q": f"code:{symbol}~ratioCode:MARKET_CAP", "size": 1, "sort": "reportDate:desc"}
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, params=params, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    market_cap = float(data[0].get("value", 0) or 0)
                    if market_cap > 0 and close_price > 0:
                        total_shares = market_cap / (close_price * 1000)
        except Exception:
            pass

    if market_cap == 0 and close_price > 0 and total_shares > 0:
        market_cap = close_price * 1000 * total_shares

    return {
        "company_name": company_name,
        "market_cap": market_cap,
        "total_shares": total_shares,
    }


def aggregate_candles(data, interval):
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
    filepath = os.path.join(BCTC_DIR, f"{symbol.upper()}.json")
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

        total_assets = bs_dict[curr_p].get("BS_TOTAL_ASSETS", bs_dict[curr_p].get("TOTAL_ASSETS", 0))
        loans = bs_dict[curr_p].get("BS_LOANS_TO_CUSTOMERS", 0)
        equity = bs_dict[curr_p].get("BS_EQUITY", bs_dict[curr_p].get("EQUITY", 0))

        nii = is_dict[curr_p].get("IS_NET_INTEREST_INCOME", 0)
        pat = is_dict[curr_p].get("IS_NET_PROFIT_AFTER_TAX", is_dict[curr_p].get("NET_PROFIT_AFTER_TAX", 0))

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
    filepath = os.path.join(BCTC_DIR, f"{symbol.upper()}.json")
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
    if not latest_period and income_statement:
        latest_period = income_statement[0].get("period")

    latest_cfo = 0
    cfo_ids = [
        "CF_NET_CASH_FLOWS_FROM_OPERATING_ACTIVITIES",
        "CF_OPERATE_CASH_FLOW",
        "CFO",
        "CF_NET_CASH"
    ]
    if cash_flow:
        for item in cash_flow:
            if latest_period and item.get("period") == latest_period and item.get("id") in cfo_ids:
                latest_cfo = item.get("value", 0)
                break
        if latest_cfo == 0:
            for item in cash_flow:
                if item.get("id") in cfo_ids:
                    latest_cfo = item.get("value", 0)
                    break

    total_liabilities = 0
    equity = 0
    if balance_sheet:
        for item in balance_sheet:
            if latest_period and item.get("period") == latest_period:
                item_id = item.get("id", "")
                val = item.get("value", 0)
                if item_id in ["BS_TOTAL_LIABILITIES", "TOTAL_LIABILITIES"]:
                    total_liabilities = val
                elif item_id in ["BS_EQUITY", "EQUITY"]:
                    equity = val

    debt_to_equity = round(total_liabilities / equity, 2) if equity > 0 else 0

    gross_profit = 0
    revenue = 0
    is_bank_or_sec = False

    if income_statement:
        for item in income_statement:
            if latest_period and item.get("period") == latest_period:
                item_id = item.get("id", "")
                val = item.get("value", 0)
                if item_id in ["IS_GROSS_PROFIT", "GROSS_PROFIT"]:
                    gross_profit = val
                elif item_id in ["IS_NET_REVENUE", "REVENUE", "NET_REVENUE", "IS_TOTAL_REVENUE"]:
                    revenue = val
                elif item_id in ["IS_NET_INTEREST_INCOME"]:
                    is_bank_or_sec = True

    if is_bank_or_sec:
        gross_margin = 0.0
    else:
        gross_margin = round((gross_profit / revenue) * 100, 1) if revenue > 0 else 0

    net_profit_ttm = 0
    pat_ids = ["IS_NET_PROFIT_AFTER_TAX", "NET_PROFIT_AFTER_TAX", "IS_PROFIT_AFTER_TAX"]
    pat_items = [item for item in income_statement if item.get("id") in pat_ids]
    if pat_items:
        pat_items = sorted(pat_items, key=lambda x: x.get("period", ""), reverse=True)
        latest_4q = pat_items[:4]
        net_profit_ttm = sum([q.get("value", 0) for q in latest_4q])

    return {
        "cfo_latest": round(latest_cfo / 1e9, 2),
        "debt_to_equity": debt_to_equity,
        "gross_margin": gross_margin,
        "net_profit_ttm": round(net_profit_ttm / 1e9, 2)
    }


def filter_and_save_cheap_stocks(stock_db):
    sector_cheap_groups = {}
    total_cheap_count = 0

    for symbol, info in stock_db.items():
        pe = info.get("pe", 0)
        pb = info.get("pb", 0)
        roe = info.get("roe", 0)
        net_profit = info.get("net_profit_ttm", 0)

        if 0 < pe <= 12 and 0 < pb <= 1.5 and roe >= 8.0 and net_profit > 0:
            sector = get_sector(symbol)
            info['sector'] = sector
            sector_cheap_groups.setdefault(sector, []).append(info)
            total_cheap_count += 1

    for sector in sector_cheap_groups:
        sector_cheap_groups[sector] = sorted(sector_cheap_groups[sector], key=lambda x: x['pe'])

    with open(CHEAP_STOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(sector_cheap_groups, f, ensure_ascii=False, indent=4)
    
    print(f"📊 Đã lọc xong: Tìm thấy tổng cộng {total_cheap_count} mã định giá rẻ phân theo nhóm ngành.")


def auto_git_push():
    try:
        print("🔄 Đang đồng bộ dữ liệu lên GitHub...")
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        pull_result = subprocess.run(
            ["git", "pull", "origin", "main", "--rebase", "--autostash"], 
            capture_output=True, text=True
        )
        if pull_result.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], check=False)
        
        subprocess.run(["git", "add", DATA_FILE], check=True)
        subprocess.run(["git", "add", LAST_UPDATE_FILE], check=True)
        subprocess.run(["git", "add", CHEAP_STOCKS_FILE], check=True)
        subprocess.run(["git", "add", HISTORY_DIR], check=True)
        if os.path.exists(BCTC_DIR):
            subprocess.run(["git", "add", BCTC_DIR], check=True)
        if os.path.exists(JS_LIB_FILE):
            subprocess.run(["git", "add", JS_LIB_FILE], check=True)

        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("ℹ️ Không có dữ liệu thay đổi nào mới để đẩy lên.")
            return

        commit_msg = f"Auto update data & cheap stocks by sector - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đẩy dữ liệu lên GitHub thành công!")
    except Exception as e:
        print(f"⚠️ Lỗi Git automation: {e}")


def main():
    if not VN100_SYMBOLS:
        print("❌ Không có danh sách mã nào để cào. Vui lòng chạy script cào danh sách trước.")
        return

    print("==================================================")
    print(f"      BƯỚC 1: CHỌN PHẠM VI MÃ ({len(VN100_SYMBOLS)} mã)      ")
    print("==================================================")
    print("1. Cào TOÀN BỘ danh sách VN100 (Mặc định)")
    print("2. Cào RIÊNG TỪNG MÃ (Tùy chọn mã cụ thể)")

    target_symbols = VN100_SYMBOLS
    mode_choice = input("Nhập lựa chọn chế độ (1/2, mặc định 1): ").strip()
    if mode_choice == '2':
        raw_input_symbols = input("Nhập mã cổ phiếu muốn cào (cách nhau bởi dấu phẩy, VD: FPT,MWG,ACB): ").strip()
        if raw_input_symbols:
            target_symbols = [s.strip().upper() for s in raw_input_symbols.split(",") if s.strip()]

    print("\n==================================================")
    print("        BƯỚC 2: CHỌN SỐ PHIÊN GIAO DỊCH         ")
    print("==================================================")
    print("1. Gần nhất: 30 phiên giao dịch gần nhất (Mặc định)")
    print("2. Dài hạn: 10 năm gần đây (~2500 phiên)")
    print("3. Tùy chỉnh: Nhập số phiên tự do")

    choice = input("Nhập lựa chọn số phiên (1/2/3, mặc định 1): ").strip()
    num_sessions = 30
    if choice == '2':
        num_sessions = 2500
    elif choice == '3':
        try:
            custom_sessions = int(input("Nhập số phiên muốn cào: ").strip())
            if custom_sessions > 0:
                num_sessions = custom_sessions
        except ValueError:
            pass

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

                history_file_path = os.path.join(HISTORY_DIR, f"{symbol.upper()}.json")
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
            print(f"⚠️ BỎ QUA {symbol}: Không lấy được giá từ API.")
            continue

        company_overview = get_company_overview(symbol, close_price)
        time.sleep(0.3)

        # 1. ƯU TIÊN LẤY TỪ API HÀNG NGÀY
        ratios = {}
        for key, code in VNDIRECT_RATIOS.items():
            val = get_vndirect_ratio(symbol, code)
            ratios[key] = val if val is not None else 0
            time.sleep(0.2)

        # 2. FALLBACK TỪ BCTC NẾU API THIẾU HOẶC BẰNG 0
        if ratios.get("pe", 0) == 0 or ratios.get("pb", 0) == 0:
            fallback_data = get_fallback_ratios_from_bctc(symbol)
            if fallback_data:
                for k, v in fallback_data.items():
                    if ratios.get(k, 0) == 0 and v != 0:
                        ratios[k] = v

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
        with open(os.path.join(HISTORY_DIR, f"{symbol.upper()}.json"), "w", encoding="utf-8") as sf:
            json.dump(symbol_history_data, sf, ensure_ascii=False)

        bctc_history = parse_bctc_history(symbol)
        adv_metrics = extract_advanced_metrics_from_bctc(symbol)
        old_data = stock_db.get(symbol, {})

        current_time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        crawled_data = {
            "symbol": symbol,
            "company_name": company_overview["company_name"],
            "market_cap": round(company_overview["market_cap"] / 1e9, 2),
            "total_shares": int(company_overview["total_shares"]),
            "close": int(close_price * 1000),
            "volume": int(volume),
            "pe": round(ratios.get("pe", 0), 2),
            "pb": round(ratios.get("pb", 0), 2),
            "ps": round(ratios.get("ps", 0), 2),
            "eps": int(ratios.get("eps", 0)),
            "roe": round(ratios.get("roe", 0) * (100 if ratios.get("roe", 0) <= 1 else 1), 1),
            "roa": round(ratios.get("roa", 0) * (100 if ratios.get("roa", 0) <= 1 else 1), 1),
            "dividend_yield": round(ratios.get("dividend_yield", 0) * (100 if ratios.get("dividend_yield", 0) <= 1 else 1), 2),
            "cfo_latest": adv_metrics["cfo_latest"],
            "debt_to_equity": adv_metrics["debt_to_equity"],
            "gross_margin": adv_metrics["gross_margin"],
            "net_profit_ttm": adv_metrics["net_profit_ttm"],
            "recommendation": status,
            "price_zone": detail,
            "updated_at": current_time_str,
            "bctc_history": bctc_history,
        }

        stock_db[symbol] = {**old_data, **crawled_data}
        time.sleep(1.0)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)

    filter_and_save_cheap_stocks(stock_db)

    crawl_timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update": crawl_timestamp}, f, ensure_ascii=False)

    print(f"✅ Đã lưu file {LAST_UPDATE_FILE} với mốc thời gian: {crawl_timestamp}")
    auto_git_push()


if __name__ == "__main__":
    main()
