from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
from ptkt import ProfessionalTechnicalAnalyzer

DATA_FILE = "data.json"
BCTC_DIR = "bctc_data"
OUTPUT_JSON = "screener_results.json"
OUTPUT_CSV = "screener_summary.csv"

# ============================================================
# PHÂN NHÓM NGÀNH CHÍNH (7 ngành)
# ============================================================
SECTOR_MAPPING = {
    "NGAN_HANG": ["ACB","BID","CTG","TCB","MBB","STB","VPB","HDB","VIB","TPB","SHB","SSB","LPB","MSB","OCB","EIB","VCB"],
    "CHUNG_KHOAN": ["SSI","VCI","HCM","VIX","MBS","FTS","BSI","CTS","ORS"],
    "BAT_DONG_SAN": ["VHM","VIC","VRE","NVL","PDR","DIG","NLG","KDH","CEO","DXG","TCH","HDG","KBC","IDC","SZC","BCM","PHR","SJS","VPI"],
    "CONG_NGHE_BAN_LE": ["FPT","MWG","PNJ","FRT","DGW"],
    "DIEN_NUOC_HA_TANG": ["POW","REE","PC1","NT2","GAS","GEG","BWE","TDM"],
    "NGUYEN_VAT_LIEU_CHU_KY": ["HPG","HSG","NKG","DGC","DCM","DPM","GVR","PHR","DHC"],
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": ["VNM","MSN","SAB","VHC","ANV","BVH","PLX","PVD","PVS","BSR","GMD","HAH","PVT","HVN","APH","ASM","DBC","KDC","MSH","PAN","SBT","DRC","CSM","BMP","DHG","CTD","VCG","HHV","GEX"],
}

# ============================================================
# PHÂN NHÓM CON (SUB-SECTOR) — ĐỂ ĐỊNH GIÁ CHÍNH XÁC
# Chỉ những mã có bản chất tài chính KHÁC với phần còn lại của ngành chính.
# ============================================================
SUB_SECTOR_MAPPING = {
    # Bảo hiểm: dùng P/B + ROE, giống ngân hàng
    "INSURANCE": ["BVH"],
    # Xăng dầu: dùng P/E thấp + biên gộp mỏng, chu kỳ giá dầu
    "PETROLEUM": ["PLX", "PVD", "PVS", "BSR"],
    # Vận tải biển: chu kỳ cước tàu, dùng P/B + P/S
    "MARITIME": ["GMD", "HAH", "PVT"],
    # Hàng không: đặc thù, CFO âm khi mở rộng đội bay
    "AVIATION": ["VJC", "HVN"],
    # Xây dựng & VLXD (trong ngành Sản xuất): dùng P/B, tránh P/E bẫy
    "CONSTRUCTION": ["CTD", "VCG", "HHV", "GEX", "DRC", "CSM", "BMP"],
    # Nông - Thủy sản: P/E + biên gộp, khá giống sản xuất
    "AGRI": ["VHC", "ANV", "DBC", "SBT", "ASM", "APH"],
}

# Cấu hình định giá cho từng nhóm (tất cả giá trị đều có thể kiểm chứng từ data.json)
SUB_SECTOR_CONFIG = {
    # Nhóm chính
    "NGAN_HANG":                    {"cap_pe": 14, "cap_pb": 1.8, "mos": 0.20, "primary_metric": "PB"},
    "CHUNG_KHOAN":                  {"cap_pe": 14, "cap_pb": 1.8, "mos": 0.25, "primary_metric": "PB"},
    "BAT_DONG_SAN":                 {"cap_pe": 12, "cap_pb": 2.0, "mos": 0.30, "primary_metric": "PB"},
    "CONG_NGHE_BAN_LE":             {"cap_pe": 20, "cap_pb": 3.0, "mos": 0.20, "primary_metric": "PE"},
    "DIEN_NUOC_HA_TANG":            {"cap_pe": 15, "cap_pb": 2.0, "mos": 0.15, "primary_metric": "PE"},
    "NGUYEN_VAT_LIEU_CHU_KY":       {"cap_pe": 12, "cap_pb": 2.0, "mos": 0.30, "primary_metric": "PB"},
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": {"cap_pe": 18, "cap_pb": 2.5, "mos": 0.25, "primary_metric": "PE"},

    # Nhóm con đặc thù
    "INSURANCE":    {"cap_pe": 16, "cap_pb": 2.0, "mos": 0.25, "primary_metric": "PB"},
    "PETROLEUM":    {"cap_pe": 12, "cap_pb": 1.5, "mos": 0.30, "primary_metric": "PE"},  # P/E thấp vì biên mỏng
    "MARITIME":     {"cap_pe": 10, "cap_pb": 1.5, "mos": 0.30, "primary_metric": "PB"},  # chu kỳ cước
    "AVIATION":     {"cap_pe": 15, "cap_pb": 3.0, "mos": 0.35, "primary_metric": "PB"},  # rủi ro cao
    "CONSTRUCTION": {"cap_pe": 12, "cap_pb": 1.5, "mos": 0.30, "primary_metric": "PB"},
    "AGRI":         {"cap_pe": 14, "cap_pb": 2.0, "mos": 0.25, "primary_metric": "PE"},
}


def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"


def get_sub_sector(symbol):
    """Trả về sub-sector nếu có, ngược lại trả về sector chính."""
    for sub, symbols in SUB_SECTOR_MAPPING.items():
        if symbol in symbols:
            return sub
    return get_sector(symbol)


def load_bctc_supplement(symbol):
    """Fallback đọc bctc_data nếu data.json thiếu PE/PB/PS."""
    bctc_path = os.path.join(BCTC_DIR, f"{symbol.upper()}.json")
    if os.path.exists(bctc_path):
        try:
            with open(bctc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ============================================================
# BƯỚC 1: LÀM SẠCH VÀ CHUẨN HÓA DỮ LIỆU TỪ data.json
# ============================================================
def normalize_stock_data(symbol, data):
    """
    Đọc data.json và trả về dict CHUẨN với đầy đủ trường dùng để tính toán.
    Tất cả giá trị fallback về 0 hoặc None — KHÔNG BAO GIỜ bịa.
    """
    # Các trường cơ bản có thể có trong data.json
    close_price = float(data.get("close", data.get("close_price", 0)) or 0)
    pe = float(data.get("pe", 0) or 0)
    pb = float(data.get("pb", 0) or 0)
    ps = float(data.get("ps", 0) or 0)
    roe = float(data.get("roe", 0) or 0)
    roa = float(data.get("roa", 0) or 0)
    eps = float(data.get("eps", 0) or 0)
    dividend_yield = float(data.get("dividend_yield", 0) or 0)
    cfo_latest = float(data.get("cfo_latest", 0) or 0)
    net_profit_ttm = float(data.get("net_profit_ttm", 0) or 0)
    debt_to_equity = float(data.get("debt_to_equity", 0) or 0)
    gross_margin = float(data.get("gross_margin", 0) or 0)

    # Fallback: PE/PB/PS từ bctc_data nếu thiếu
    if pe == 0 or pb == 0 or ps == 0:
        supp = load_bctc_supplement(symbol)
        ratios_list = supp.get("ratios", [])
        if ratios_list:
            latest = ratios_list[0]
            if pe == 0: pe = float(latest.get("PE") or latest.get("PRICE_TO_EARNINGS") or 0)
            if pb == 0: pb = float(latest.get("PB") or latest.get("PRICE_TO_BOOK") or 0)
            if ps == 0: ps = float(latest.get("PS") or latest.get("PRICE_TO_SALES") or 0)

    # Suy EPS từ close/PE nếu eps = 0 nhưng có PE
    if eps == 0 and pe > 0 and close_price > 0:
        eps = close_price / pe

    # Suy BVPS từ close/PB
    bvps = (close_price / pb) if pb > 0 and close_price > 0 else 0

    # Tăng trưởng từ bctc_history
    profit_growth_yoy = 0.0
    credit_growth_yoy = 0.0
    bctc_history = data.get("bctc_history", [])
    if bctc_history and isinstance(bctc_history, list):
        latest = bctc_history[0]
        profit_growth_yoy = float(latest.get("profit_growth_yoy", 0) or 0)
        credit_growth_yoy = float(latest.get("credit_growth_yoy", 0) or 0)

    return {
        "close_price": close_price,
        "pe": pe, "pb": pb, "ps": ps,
        "roe": roe, "roa": roa,
        "eps": eps, "bvps": bvps,
        "dividend_yield": dividend_yield,
        "cfo_latest": cfo_latest,
        "net_profit_ttm": net_profit_ttm,
        "debt_to_equity": debt_to_equity,
        "gross_margin": gross_margin,
        "profit_growth_yoy": profit_growth_yoy,
        "credit_growth_yoy": credit_growth_yoy,
    }


# ============================================================
# BƯỚC 2: TÍNH MEDIAN NGÀNH TỪ CHÍNH data.json
# ============================================================
def compute_sector_medians(normalized_db):
    """
    Tính median P/E, P/B, P/S, ROE của từng sub-sector (dùng sub-sector để chính xác hơn).
    Nếu sub-sector có < 3 mã → fallback về sector chính.
    """
    buckets = {}
    for symbol, nd in normalized_db.items():
        sub = get_sub_sector(symbol)
        sector = get_sector(symbol)
        for key in (sub, sector):
            b = buckets.setdefault(key, {"pe": [], "pb": [], "ps": [], "roe": []})
            if nd["pe"] > 0: b["pe"].append(nd["pe"])
            if nd["pb"] > 0: b["pb"].append(nd["pb"])
            if nd["ps"] > 0: b["ps"].append(nd["ps"])
            if nd["roe"] != 0: b["roe"].append(nd["roe"])

    medians = {}
    for key, b in buckets.items():
        n = len(b["pe"]) + len(b["pb"])
        if n < 3:
            continue  # bỏ qua bucket quá nhỏ
        medians[key] = {
            "pe": float(np.median(b["pe"])) if b["pe"] else 0.0,
            "pb": float(np.median(b["pb"])) if b["pb"] else 0.0,
            "ps": float(np.median(b["ps"])) if b["ps"] else 0.0,
            "roe": float(np.median(b["roe"])) if b["roe"] else 0.0,
            "n": n,
        }
    return medians


def get_median_for_symbol(symbol, sector_medians):
    """Ưu tiên median sub-sector; nếu không có, fallback về sector chính; cuối cùng là giá trị mặc định."""
    sub = get_sub_sector(symbol)
    sector = get_sector(symbol)
    if sub in sector_medians and sector_medians[sub]["n"] >= 3:
        return sector_medians[sub], sub
    if sector in sector_medians:
        return sector_medians[sector], sector
    return {"pe": 12.0, "pb": 2.0, "ps": 1.5, "roe": 12.0, "n": 0}, sector


# ============================================================
# BƯỚC 3: TÍNH VÙNG MUA THEO TỪNG NHÓM
# ============================================================
def compute_fair_value_zone(symbol, nd, sector_median, config, group_label):
    """
    Tính vùng mua bằng 3-4 phương pháp, TẤT CẢ đều dùng dữ liệu có trong data.json.

    Input bắt buộc:
      - nd["eps"], nd["bvps"]: từ data.json (hoặc suy từ close/PE, close/PB)
      - sector_median["pe"], ["pb"]: median ngành
      - config: cấu hình theo nhóm (cap_pe, cap_pb, mos)
    """
    eps = nd["eps"]
    bvps = nd["bvps"]
    close = nd["close_price"]
    pe = nd["pe"]
    pb = nd["pb"]
    roe = nd["roe"]
    cfo = nd["cfo_latest"]
    npat = nd["net_profit_ttm"]
    ps = nd["ps"]

    methods = {}
    med_pe = sector_median.get("pe") or 12.0
    med_pb = sector_median.get("pb") or 2.0
    med_roe = sector_median.get("roe") or 0.0

    cap_pe = config["cap_pe"]
    cap_pb = config["cap_pb"]
    mos = config["mos"]
    is_financial = group_label in ("NGAN_HANG", "CHUNG_KHOAN", "INSURANCE")

    # ---- Phương pháp A: P/E method (nếu EPS > 0) ----
    if eps > 0 and med_pe > 0:
        # Thưởng 15% nếu ROE > median (doanh nghiệp tốt hơn trung bình ngành)
        roe_bonus = 1.15 if (roe > 0 and roe > med_roe) else 1.0
        rational_pe = min(med_pe * roe_bonus, cap_pe)
        methods["PE_method"] = round(eps * rational_pe, 0)

    # ---- Phương pháp B: P/B method (nếu BVPS > 0) ----
    if bvps > 0 and med_pb > 0:
        rational_pb = min(med_pb, cap_pb)
        methods["PB_method"] = round(bvps * rational_pb, 0)

    # ---- Phương pháp C: Graham Number (chỉ phi tài chính) ----
    if not is_financial and eps > 0 and bvps > 0:
        graham = (22.5 * eps * bvps) ** 0.5
        methods["Graham"] = round(graham, 0)

    # ---- Phương pháp D: CFO boost (chất lượng lợi nhuận) ----
    if not is_financial and npat > 0 and cfo > 0 and (cfo / npat) >= 0.8 and eps > 0 and med_pe > 0:
        rational_pe = min(med_pe, cap_pe)
        methods["CFO_boost"] = round(eps * rational_pe * 1.10, 0)

    # ---- Phương pháp E: P/S method (dùng cho ngành bán lẻ, chu kỳ, BĐS) ----
    if config["primary_metric"] in ("PB",) and ps > 0 and sector_median.get("ps", 0) > 0:
        # Suy doanh thu/cp từ close/PS → áp P/S mục tiêu
        sales_per_share = close / ps if ps > 0 else 0
        target_ps = min(sector_median["ps"], 2.5)
        if sales_per_share > 0:
            methods["PS_method"] = round(sales_per_share * target_ps, 0)

    if not methods:
        return {
            "fair_low": 0, "fair_high": 0, "graham": 0,
            "methods": {}, "mos_pct": round(mos * 100, 1),
            "rationale": "Không đủ dữ liệu (thiếu EPS, BVPS, hoặc median ngành).",
            "discount_to_fair_pct": 0,
            "verdict": "KHÔNG ĐỦ DỮ LIỆU",
        }

    # ---- Lấy trung vị có trọng số ----
    weights = {"PE_method": 2, "PB_method": 1.5, "Graham": 2, "CFO_boost": 1, "PS_method": 1}
    weighted = []
    for k, v in methods.items():
        weighted.extend([v] * int(weights.get(k, 1) * 2))
    weighted.sort()
    n = len(weighted)
    fair_high = weighted[n // 2] if n % 2 else (weighted[n // 2 - 1] + weighted[n // 2]) / 2

    # ---- Trừ biên an toàn ----
    fair_low = fair_high * (1 - mos)

    # ---- So sánh giá hiện tại ----
    discount_to_fair = ((fair_low - close) / close * 100) if close > 0 else 0.0

    if close <= 0:
        verdict = "KHÔNG CÓ GIÁ"
    elif close <= fair_low:
        verdict = "RẺ - TRONG VÙNG MUA"
    elif close <= fair_high:
        verdict = "HỢP LÝ - CHỜ ĐIỀU CHỈNH"
    elif close <= fair_high * 1.2:
        verdict = "HƠI ĐẮT - KHÔNG MUA"
    else:
        verdict = "ĐẮT - TRÁNH"

    rationale = (
        f"[{group_label}] "
        f"PE_method={methods.get('PE_method', 0):,.0f} "
        f"(P/E lý tưởng {min(med_pe * (1.15 if roe > med_roe else 1.0), cap_pe):.1f}x, "
        f"median {med_pe:.1f}x); "
        f"PB_method={methods.get('PB_method', 0):,.0f} "
        f"(P/B lý tưởng {min(med_pb, cap_pb):.1f}x, median {med_pb:.1f}x); "
        + (f"Graham={methods.get('Graham', 0):,.0f}; " if "Graham" in methods else "")
        + (f"PS_method={methods.get('PS_method', 0):,.0f}; " if "PS_method" in methods else "")
        + f"MoS {mos*100:.0f}%."
    )

    return {
        "fair_low": round(fair_low, 0),
        "fair_high": round(fair_high, 0),
        "graham": round(methods.get("Graham", 0), 0),
        "methods": {k: round(v, 0) for k, v in methods.items()},
        "mos_pct": round(mos * 100, 1),
        "rationale": rationale,
        "discount_to_fair_pct": round(discount_to_fair, 1),
        "verdict": verdict,
    }


# ============================================================
# BƯỚC 4: ĐÁNH GIÁ TỪNG MÃ
# ============================================================
def evaluate_stock(symbol, nd, sector_median, group_label, config):
    sector = get_sector(symbol)

    pe = nd["pe"]
    pb = nd["pb"]
    ps = nd["ps"]
    roe = nd["roe"]
    roa = nd["roa"]
    dividend_yield = nd["dividend_yield"]
    close_price = nd["close_price"]
    cfo_latest = nd["cfo_latest"]
    net_profit_ttm = nd["net_profit_ttm"]
    debt_to_equity = nd["debt_to_equity"]
    gross_margin = nd["gross_margin"]
    profit_growth_yoy = nd["profit_growth_yoy"]
    credit_growth_yoy = nd["credit_growth_yoy"]

    # ============ 1. ĐIỂM CƠ BẢN (50đ) ============
    fundamental_score = 0
    fund_notes = []

    if sector == "NGAN_HANG":
        if credit_growth_yoy >= 12:
            fundamental_score += 18; fund_notes.append("Tín dụng mạnh (>=12%)")
        elif credit_growth_yoy >= 8:
            fundamental_score += 10; fund_notes.append("Tín dụng khá")
        if roe >= 18:
            fundamental_score += 17; fund_notes.append("ROE xuất sắc (>=18%)")
        elif roe >= 14:
            fundamental_score += 10; fund_notes.append("ROE tốt (>=14%)")
    elif sector == "CHUNG_KHOAN":
        if profit_growth_yoy >= 20:
            fundamental_score += 20; fund_notes.append("LN tăng trưởng mạnh (>=20%)")
        elif profit_growth_yoy >= 10:
            fundamental_score += 10; fund_notes.append("LN hồi phục tốt")
        if roe >= 15:
            fundamental_score += 15; fund_notes.append("ROE ngành CK cao (>=15%)")
        elif roe >= 10:
            fundamental_score += 8; fund_notes.append("ROE ổn định")
    elif sector == "BAT_DONG_SAN":
        if profit_growth_yoy >= 10:
            fundamental_score += 15; fund_notes.append("LN duy trì tăng trưởng")
        if roe >= 12:
            fundamental_score += 20; fund_notes.append("ROE BĐS đạt chuẩn (>=12%)")
        elif roe > 0:
            fundamental_score += 10; fund_notes.append("Có lãi dương")
    elif sector == "CONG_NGHE_BAN_LE":
        if profit_growth_yoy >= 20:
            fundamental_score += 18; fund_notes.append("Tăng trưởng lõi mạnh (>=20%)")
        elif profit_growth_yoy >= 10:
            fundamental_score += 10; fund_notes.append("Tăng trưởng ổn định")
        if roe >= 18:
            fundamental_score += 17; fund_notes.append("ROE xuất sắc")
        elif roe >= 12:
            fundamental_score += 10; fund_notes.append("ROE tốt")
    elif sector == "DIEN_NUOC_HA_TANG":
        if dividend_yield >= 6.0:
            fundamental_score += 20; fund_notes.append(f"Cổ tức hấp dẫn ({dividend_yield}%)")
        elif dividend_yield > 0:
            fundamental_score += 10; fund_notes.append(f"Có cổ tức ({dividend_yield}%)")
        if roe >= 10:
            fundamental_score += 15; fund_notes.append("ROE ổn định phòng thủ")
        else:
            fundamental_score += 8
    elif sector == "NGUYEN_VAT_LIEU_CHU_KY":
        if profit_growth_yoy >= 15:
            fundamental_score += 18; fund_notes.append("Hưởng lợi chu kỳ")
        elif profit_growth_yoy >= 0:
            fundamental_score += 10; fund_notes.append("Duy trì nhịp cơ bản")
        if roe >= 12:
            fundamental_score += 17; fund_notes.append("ROE chu kỳ tốt")
        else:
            fundamental_score += 8
    else:
        if profit_growth_yoy >= 10:
            fundamental_score += 15; fund_notes.append("LN tăng trưởng tốt")
        elif profit_growth_yoy >= 0:
            fundamental_score += 8; fund_notes.append("LN ổn định")
        if roe >= 14:
            fundamental_score += 20; fund_notes.append("ROE sản xuất cao (>=14%)")
        elif roe >= 10:
            fundamental_score += 10; fund_notes.append("ROE khá")

    if roa >= 5.0:
        fundamental_score += 5; fund_notes.append(f"ROA cao ({roa}%)")
    elif roa >= 2.5:
        fundamental_score += 3; fund_notes.append(f"ROA tốt ({roa}%)")

    if sector not in ["NGAN_HANG", "CHUNG_KHOAN"]:
        if cfo_latest > 0 and (net_profit_ttm <= 0 or cfo_latest >= net_profit_ttm * 0.8):
            fundamental_score += 5; fund_notes.append("CFO mạnh mẽ")
        elif cfo_latest < 0:
            fundamental_score -= 5; fund_notes.append("⚠️ CFO âm")
        if 0 < debt_to_equity <= 1.0:
            fundamental_score += 5; fund_notes.append(f"D/E an toàn ({debt_to_equity})")
        elif debt_to_equity > 2.5:
            fundamental_score -= 5; fund_notes.append(f"⚠️ D/E cao ({debt_to_equity})")
    else:
        fundamental_score += 5
        fund_notes.append("Ngân hàng tối ưu vốn")

    fundamental_score = int(np.clip(fundamental_score, 0, 50))

    # ============ 2. ĐIỂM ĐỊNH GIÁ (30đ) ============
    valuation_score = 0
    if sector == "BAT_DONG_SAN":
        if (0 < pb < 1.5) or (0 < ps < 2.0): valuation_score = 30
        elif (0 < pb < 2.2) or (0 < ps < 3.5): valuation_score = 18
        else: valuation_score = 8
    elif sector == "NGUYEN_VAT_LIEU_CHU_KY":
        if (0 < ps < 1.2) or (0 < pe < 12): valuation_score = 30
        elif (0 < ps < 2.0) or (0 < pe < 18): valuation_score = 18
        else: valuation_score = 8
    elif sector == "CONG_NGHE_BAN_LE":
        if 0 < pe < 18 or (profit_growth_yoy > 20 and pe < 25): valuation_score = 30
        elif 0 < pe < 25: valuation_score = 18
        else: valuation_score = 8
    elif sector in ["NGAN_HANG", "CHUNG_KHOAN"]:
        if 0 < pb < 1.3 or (roe >= 16 and pb < 1.8): valuation_score = 30
        elif 0 < pb < 2.0: valuation_score = 18
        else: valuation_score = 8
    else:
        if 0 < pe < 15 or dividend_yield >= 5.0: valuation_score = 30
        elif 0 < pe < 20 or dividend_yield >= 3.0: valuation_score = 18
        else: valuation_score = 8
    valuation_score = int(np.clip(valuation_score, 0, 30))

    # ============ 3. ĐIỂM KỸ THUẬT (20đ) ============
    technical_score_raw = 50
    technical_status = "Tích lũy sideway"
    pattern = "Tích lũy"
    volume_analysis = "Chưa phân tích volume"

    history_path = f"history/{symbol.upper()}.json"
    if os.path.exists(history_path):
        try:
            analyzer = ProfessionalTechnicalAnalyzer(history_path)
            ptkt_res = analyzer.analyze()
            technical_score_raw = ptkt_res.get("technical_score", 50)
            technical_status = ptkt_res.get("technical_status", "Tích lũy sideway")
            pattern = ptkt_res.get("pattern", "Tích lũy")
            volume_analysis = ptkt_res.get("volume_analysis", "")
        except Exception as e:
            print(f"⚠️ Lỗi PTKT {symbol}: {e}")

    technical_score = int(round((technical_score_raw / 100.0) * 20))
    technical_score = int(np.clip(technical_score, 0, 20))

    total_score = fundamental_score + valuation_score + technical_score

    potential_zone = "THEO DÕI THÊM"
    if total_score >= 75:
        potential_zone = "VÙNG TÍCH SẢN TỐI ƯU (A+)"
    elif total_score >= 60:
        potential_zone = "VÙNG MUA AN TOÀN (B)"

    # ============ 💰 VÙNG MUA ============
    fv = compute_fair_value_zone(symbol, nd, sector_median, config, group_label)

    return {
        "symbol": symbol,
        "sector": sector,
        "sub_sector": group_label,
        "close_price": close_price,
        "pe": pe, "pb": pb, "ps": ps,
        "roe": roe, "roa": roa, "eps": nd["eps"], "bvps": round(nd["bvps"], 0),
        "dividend_yield": dividend_yield,
        "profit_growth_yoy": profit_growth_yoy,
        "cfo_latest": cfo_latest,
        "debt_to_equity": debt_to_equity,
        "gross_margin": gross_margin,
        "fundamental_score": fundamental_score,
        "valuation_score": valuation_score,
        "technical_score": technical_score,
        "total_score": total_score,
        "potential_zone": potential_zone,
        "pattern": pattern,
        "technical_status": technical_status,
        "volume_analysis": volume_analysis,
        "fundamental_notes": " | ".join(fund_notes),

        # 💰 Vùng mua (deterministic — dùng dữ liệu từ data.json)
        "fair_value_high": fv["fair_high"],
        "fair_value_low": fv["fair_low"],
        "graham_number": fv["graham"],
        "margin_of_safety_pct": fv["mos_pct"],
        "fair_value_methods": fv["methods"],
        "fair_value_rationale": fv["rationale"],
        "discount_to_fair_pct": fv["discount_to_fair_pct"],
        "valuation_verdict": fv["verdict"],
    }


# ============================================================
# MAIN
# ============================================================
def main():
    print("🚀 Bộ lọc Quant + Vùng mua deterministic (100% từ data.json)...")

    if not os.path.exists(DATA_FILE):
        print(f"⚠️ Không tìm thấy {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    # Bước 1: Chuẩn hóa dữ liệu
    normalized_db = {}
    for symbol, raw in stock_db.items():
        normalized_db[symbol] = normalize_stock_data(symbol, raw)

    # Bước 2: Tính median ngành & sub-ngành
    print("📊 Đang tính median ngành...")
    sector_medians = compute_sector_medians(normalized_db)
    for sec, m in sector_medians.items():
        print(f"   [{sec:18s}] n={m['n']:2d} | P/E={m['pe']:6.2f} | P/B={m['pb']:5.2f} | ROE={m['roe']:5.1f}%")

    # Bước 3: Đánh giá từng mã
    results = []
    for symbol, nd in normalized_db.items():
        sector = get_sector(symbol)
        group_label = get_sub_sector(symbol)
        # Lấy config: ưu tiên sub-sector, fallback về sector chính
        if group_label in SUB_SECTOR_CONFIG:
            config = SUB_SECTOR_CONFIG[group_label]
        else:
            config = SUB_SECTOR_CONFIG.get(sector, SUB_SECTOR_CONFIG["SAN_XUAT_TIEU_DUNG_PHONG_THU"])

        median, median_label = get_median_for_symbol(symbol, sector_medians)
        res = evaluate_stock(symbol, nd, median, group_label, config)
        if res:
            results.append(res)

    if not results:
        print("⚠️ Không có kết quả.")
        return

    results = sorted(results, key=lambda x: (x.get("total_score", 0), x.get("fundamental_score", 0)), reverse=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n✅ Hoàn tất!")
    print(f"   - {OUTPUT_JSON}")
    print(f"   - {OUTPUT_CSV}")

    # In top 10 vùng mua hấp dẫn
    print("\n💰 TOP 10 MÃ ĐANG TRONG VÙNG MUA (giá <= fair_low):")
    cheap = [r for r in results if r["valuation_verdict"] == "RẺ - TRONG VÙNG MUA"]
    cheap.sort(key=lambda x: x["discount_to_fair_pct"], reverse=True)
    for r in cheap[:10]:
        print(f"   {r['symbol']:5s} [{r['sub_sector']:14s}] | "
              f"Giá {r['close_price']:>10,.0f} | "
              f"Mua <= {r['fair_value_low']:>10,.0f} | "
              f"Fair {r['fair_value_high']:>10,.0f} | "
              f"CK {r['discount_to_fair_pct']:>5.1f}% | Điểm {r['total_score']}")

    # Cảnh báo mã đắt
    print("\n⚠️ TOP 5 MÃ ĐẮT (nên tránh):")
    expensive = [r for r in results if r["valuation_verdict"] == "ĐẮT - TRÁNH"]
    expensive.sort(key=lambda x: x["close_price"] / max(x["fair_value_high"], 1), reverse=True)
    for r in expensive[:5]:
        print(f"   {r['symbol']:5s} | Giá {r['close_price']:>10,.0f} | Fair {r['fair_value_high']:>10,.0f} | Điểm {r['total_score']}")


if __name__ == "__main__":
    main()
