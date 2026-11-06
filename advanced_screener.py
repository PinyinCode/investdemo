from datetime import datetime
import json
import os
import shutil
import numpy as np
import pandas as pd
from ptkt import ProfessionalTechnicalAnalyzer

DATA_FILE = "data.json"
BCTC_DIR = "bctc_data"
OUTPUT_JSON = "screener_results.json"
OUTPUT_CSV = "screener_summary.csv"

# Các trường AI KHÔNG BAO GIỜ ĐƯỢC GHI ĐÈ
AI_FIELDS = {
    "bctc", "catalyst", "risks", "outlook", "macro_view",
    "ai_recommendation", "ai_price_zone", "ai_updated_at",
    "recommendation", "price_zone", "updated_at",
    "bctc_history",
}

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
# PHÂN NHÓM CON (SUB-SECTOR)
# ============================================================
SUB_SECTOR_MAPPING = {
    "INSURANCE": ["BVH"],
    "PETROLEUM": ["PLX", "PVD", "PVS", "BSR"],
    "MARITIME": ["GMD", "HAH", "PVT"],
    "AVIATION": ["VJC", "HVN"],
    "CONSTRUCTION": ["CTD", "VCG", "HHV", "GEX", "DRC", "CSM", "BMP"],
    "AGRI": ["VHC", "ANV", "DBC", "SBT", "ASM", "APH"],
}

SUB_SECTOR_CONFIG = {
    "NGAN_HANG":                    {"cap_pe": 14, "cap_pb": 1.8, "mos": 0.20, "primary_metric": "PB"},
    "CHUNG_KHOAN":                  {"cap_pe": 14, "cap_pb": 1.8, "mos": 0.25, "primary_metric": "PB"},
    "BAT_DONG_SAN":                 {"cap_pe": 12, "cap_pb": 2.0, "mos": 0.30, "primary_metric": "PB"},
    "CONG_NGHE_BAN_LE":             {"cap_pe": 20, "cap_pb": 3.0, "mos": 0.20, "primary_metric": "PE"},
    "DIEN_NUOC_HA_TANG":            {"cap_pe": 15, "cap_pb": 2.0, "mos": 0.15, "primary_metric": "PE"},
    "NGUYEN_VAT_LIEU_CHU_KY":       {"cap_pe": 12, "cap_pb": 2.0, "mos": 0.30, "primary_metric": "PB"},
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": {"cap_pe": 18, "cap_pb": 2.5, "mos": 0.25, "primary_metric": "PE"},

    "INSURANCE":    {"cap_pe": 16, "cap_pb": 2.0, "mos": 0.25, "primary_metric": "PB"},
    "PETROLEUM":    {"cap_pe": 12, "cap_pb": 1.5, "mos": 0.30, "primary_metric": "PE"},
    "MARITIME":     {"cap_pe": 10, "cap_pb": 1.5, "mos": 0.30, "primary_metric": "PB"},
    "AVIATION":     {"cap_pe": 15, "cap_pb": 3.0, "mos": 0.35, "primary_metric": "PB"},
    "CONSTRUCTION": {"cap_pe": 12, "cap_pb": 1.5, "mos": 0.30, "primary_metric": "PB"},
    "AGRI":         {"cap_pe": 14, "cap_pb": 2.0, "mos": 0.25, "primary_metric": "PE"},
}


def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"


def get_sub_sector(symbol):
    for sub, symbols in SUB_SECTOR_MAPPING.items():
        if symbol in symbols:
            return sub
    return get_sector(symbol)


def load_bctc_supplement(symbol):
    bctc_path = os.path.join(BCTC_DIR, f"{symbol.upper()}.json")
    if os.path.exists(bctc_path):
        try:
            with open(bctc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ============================================================
# BƯỚC 1: CHUẨN HÓA DỮ LIỆU
# ============================================================
def normalize_stock_data(symbol, data):
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

    if pe == 0 or pb == 0 or ps == 0:
        supp = load_bctc_supplement(symbol)
        ratios_list = supp.get("ratios", [])
        if ratios_list:
            latest = ratios_list[0]
            if pe == 0: pe = float(latest.get("PE") or latest.get("PRICE_TO_EARNINGS") or 0)
            if pb == 0: pb = float(latest.get("PB") or latest.get("PRICE_TO_BOOK") or 0)
            if ps == 0: ps = float(latest.get("PS") or latest.get("PRICE_TO_SALES") or 0)

    if eps == 0 and pe > 0 and close_price > 0:
        eps = close_price / pe

    bvps = (close_price / pb) if pb > 0 and close_price > 0 else 0

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
# BƯỚC 2: MEDIAN NGÀNH
# ============================================================
def compute_sector_medians(normalized_db):
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
            continue
        medians[key] = {
            "pe": float(np.median(b["pe"])) if b["pe"] else 0.0,
            "pb": float(np.median(b["pb"])) if b["pb"] else 0.0,
            "ps": float(np.median(b["ps"])) if b["ps"] else 0.0,
            "roe": float(np.median(b["roe"])) if b["roe"] else 0.0,
            "n": n,
        }
    return medians


def get_median_for_symbol(symbol, sector_medians):
    sub = get_sub_sector(symbol)
    sector = get_sector(symbol)
    if sub in sector_medians and sector_medians[sub]["n"] >= 3:
        return sector_medians[sub], sub
    if sector in sector_medians:
        return sector_medians[sector], sector
    return {"pe": 12.0, "pb": 2.0, "ps": 1.5, "roe": 12.0, "n": 0}, sector


# ============================================================
# BƯỚC 3: TÍNH VÙNG MUA
# ============================================================
def compute_fair_value_zone(symbol, nd, sector_median, config, group_label):
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

    if eps > 0 and med_pe > 0:
        roe_bonus = 1.15 if (roe > 0 and roe > med_roe) else 1.0
        rational_pe = min(med_pe * roe_bonus, cap_pe)
        methods["PE_method"] = round(eps * rational_pe, 0)

    if bvps > 0 and med_pb > 0:
        rational_pb = min(med_pb, cap_pb)
        methods["PB_method"] = round(bvps * rational_pb, 0)

    if not is_financial and eps > 0 and bvps > 0:
        graham = (22.5 * eps * bvps) ** 0.5
        methods["Graham"] = round(graham, 0)

    if not is_financial and npat > 0 and cfo > 0 and (cfo / npat) >= 0.8 and eps > 0 and med_pe > 0:
        rational_pe = min(med_pe, cap_pe)
        methods["CFO_boost"] = round(eps * rational_pe * 1.10, 0)

    if config["primary_metric"] in ("PB",) and ps > 0 and sector_median.get("ps", 0) > 0:
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

    weights = {"PE_method": 2, "PB_method": 1.5, "Graham": 2, "CFO_boost": 1, "PS_method": 1}
    weighted = []
    for k, v in methods.items():
        weighted.extend([v] * int(weights.get(k, 1) * 2))
    weighted.sort()
    n = len(weighted)
    fair_high = weighted[n // 2] if n % 2 else (weighted[n // 2 - 1] + weighted[n // 2]) / 2

    fair_low = fair_high * (1 - mos)
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
# 🎯 BƯỚC 3.5: QUYẾT ĐỊNH CUỐI CÙNG — CẦN ĐỦ 4 YẾU TỐ
# ============================================================
def compute_final_decision(fund_score, tech_score, val_score, total_score,
                           verdict, cfo, npat, roe, debt_to_equity,
                           discount_to_fair_pct=0.0, close_price=0.0,
                           fair_high=0.0, fair_low=0.0):
    is_bank_or_sec = roe > 0 and debt_to_equity > 3.0

    # ============================================================
    # RULE 0: KIỂM TRA CÁC TRƯỜNG HỢP ĐẶC BIỆT
    # ============================================================
    if fund_score < 20:
        return ("❌ TRÁNH", "rose", f"PTCB chỉ {fund_score}/50 — doanh nghiệp yếu về cơ bản. Không mua dù giá rẻ.")

    if not is_bank_or_sec and cfo < 0 and npat > 0 and fund_score < 25:
        return ("⚠️ CẢNH BÁO LỢI NHUẬN ẢO", "amber", f"CFO âm ({cfo:,.0f} tỷ) trong khi LNST dương ({npat:,.0f} tỷ) — lợi nhuận không có tiền mặt thật.")

    # Nếu giá quá đắt so với Fair Value (vượt xa fair_high > 20%)
    if close_price > 0 and fair_high > 0 and close_price > fair_high * 1.2:
        return ("❌ TRÁNH", "rose", f"Giá {close_price:,.0f} đã vượt xa fair_high {fair_high:,.0f} quá nhiều. Định giá quá đắt so với giá trị thực.")

    # Nếu doanh nghiệp cơ bản tốt nhưng giá đang cao hơn fair_high -> Chờ
    if close_price > 0 and fair_high > 0 and close_price > fair_high:
        return ("⚠️ CHỜ VỀ VÙNG MUA", "amber", f"Giá {close_price:,.0f} cao hơn fair_high {fair_high:,.0f}. Doanh nghiệp tốt (PTCB {fund_score}/50) nhưng định giá đã đắt, chờ điều chỉnh.")

    # ============================================================
    # RULE 1: MUA MẠNH
    # ============================================================
    if (verdict == "RẺ - TRONG VÙNG MUA" and fund_score >= 40 and tech_score >= 15 and val_score >= 24 and total_score >= 75 and discount_to_fair_pct >= 5):
        return ("🎯 MUA MẠNH", "emerald", f"ĐỦ 4 YẾU TỐ: Vùng mua (CK {discount_to_fair_pct:.1f}%) + PTCB {fund_score}/50 + PTKT {tech_score}/20 + Định giá {val_score}/30 + Tổng {total_score}đ. Setup lý tưởng.")

    # ============================================================
    # RULE 2: MUA TÍCH SẢN
    # ============================================================
    if (verdict == "RẺ - TRONG VÙNG MUA" and fund_score >= 30 and tech_score >= 10 and val_score >= 18 and total_score >= 60):
        return ("✅ MUA TÍCH SẢN", "emerald", f"ĐỦ 4 YẾU TỐ: Vùng mua (CK {discount_to_fair_pct:.1f}%) + PTCB {fund_score}/50 + PTKT {tech_score}/20 + Định giá {val_score}/30 + Tổng {total_score}đ. Có thể giải ngân từng phần.")

    # ============================================================
    # RULE 3: CHỜ VỀ VÙNG MUA
    # ============================================================
    if (fund_score >= 30 and val_score >= 18 and verdict in ("HỢP LÝ - CHỜ ĐIỀU CHỈNH", "HƠI ĐẮT - KHÔNG MUA")):
        return ("⚠️ CHỜ VỀ VÙNG MUA", "amber", f"Doanh nghiệp tốt (PTCB {fund_score}/50, Định giá {val_score}/30) nhưng giá chưa rẻ. Chờ điều chỉnh về fair_low mới mua.")

    # ============================================================
    # RULE 4: CHỜ XÁC NHẬN KỸ THUẬT
    # ============================================================
    if (verdict == "RẺ - TRONG VÙNG MUA" and fund_score >= 30 and val_score >= 18 and tech_score < 10):
        return ("⏳ CHỜ XÁC NHẬN KỸ THUẬT", "amber", f"Đã đủ 3/4 yếu tố (Vùng mua + PTCB {fund_score}/50 + Định giá {val_score}/30) nhưng PTKT yếu ({tech_score}/20). Chờ tín hiệu đảo chiều trước khi mua.")

    # ============================================================
    # RULE 5: CHỜ ĐỊNH GIÁ TỐT HƠN
    # ============================================================
    if (verdict == "RẺ - TRONG VÙNG MUA" and fund_score >= 30 and val_score < 18):
        return ("⏳ CHỜ ĐỊNH GIÁ TỐT HƠN", "amber", f"Giá trong vùng mua + PTCB {fund_score}/50 tốt, nhưng điểm định giá chỉ {val_score}/30 (P/E, P/B chưa thực sự rẻ so với ngành).")

    # ============================================================
    # RULE 6: THEO DÕI
    # ============================================================
    missing = []
    if verdict != "RẺ - TRONG VÙNG MUA": missing.append(f"giá chưa vào vùng mua ({verdict})")
    if fund_score < 30: missing.append(f"PTCB {fund_score}/50 < 30")
    if tech_score < 10: missing.append(f"PTKT {tech_score}/20 < 10")
    if val_score < 18: missing.append(f"Định giá {val_score}/30 < 18")

    return ("👀 THEO DÕI", "slate", f"Chưa đủ điều kiện: {', '.join(missing) if missing else 'cần thêm thời gian'}.")


# ============================================================
# BƯỚC 4: ĐÁNH GIÁ TỪNG MÃ
# ============================================================
def evaluate_stock(symbol, nd, sector_median, group_label, config):
    sector = get_sector(symbol)

    pe = nd["pe"]; pb = nd["pb"]; ps = nd["ps"]
    roe = nd["roe"]; roa = nd["roa"]
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
        else:
            fundamental_score -= 15; fund_notes.append("⚠️ LNST tăng trưởng âm (suy thoái chu kỳ)")
            
        if roe >= 12:
            fundamental_score += 17; fund_notes.append("ROE chu kỳ tốt")
        else:
            fundamental_score += 8
    else:
        if profit_growth_yoy >= 10:
            fundamental_score += 15; fund_notes.append("LN tăng trưởng tốt")
        elif profit_growth_yoy >= 0:
            fundamental_score += 8; fund_notes.append("LN ổn định")
        else:
            fundamental_score -= 10; fund_notes.append("⚠️ LNST tăng trưởng âm")
            
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

    # ============ 🎯 TÍNH VÙNG MUA & QUYẾT ĐỊNH CUỐI CÙNG ============
    fv = compute_fair_value_zone(symbol, nd, sector_median, config, group_label)

    final_decision, final_color, final_reason = compute_final_decision(
        fund_score=fundamental_score,
        tech_score=technical_score,
        val_score=valuation_score,
        total_score=total_score,
        verdict=fv["verdict"],
        cfo=cfo_latest,
        npat=net_profit_ttm,
        roe=roe,
        debt_to_equity=debt_to_equity,
        discount_to_fair_pct=fv["discount_to_fair_pct"],
        close_price=close_price,
        fair_high=fv["fair_high"],
        fair_low=fv["fair_low"]
    )

    return {
        "symbol": symbol,
        "sector": sector,
        "sub_sector": group_label,
        "close_price": close_price,
        "pe": pe, "pb": pb, "ps": ps,
        "roe": roe, "roa": roa, "eps": round(nd["eps"], 0), "bvps": round(nd["bvps"], 0),
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

        "fair_value_high": fv["fair_high"],
        "fair_value_low": fv["fair_low"],
        "graham_number": fv["graham"],
        "margin_of_safety_pct": fv["mos_pct"],
        "fair_value_methods": fv["methods"],
        "fair_value_rationale": fv["rationale"],
        "discount_to_fair_pct": fv["discount_to_fair_pct"],
        "valuation_verdict": fv["verdict"],

        # 🆕 Quyết định cuối cùng
        "final_decision": final_decision,
        "final_decision_color": final_color,
        "final_decision_reason": final_reason,
    }


# ============================================================
# BƯỚC 5: GHI CÁC TRƯỜNG MỚI VÀO data.json
# ============================================================
def update_data_json_with_valuation(normalized_db, sector_medians):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_db = json.load(f)

    backup_path = f"{DATA_FILE}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(DATA_FILE, backup_path)
    print(f"   🔒 Backup: {backup_path}")

    updated = 0
    for symbol, raw in raw_db.items():
        if symbol not in normalized_db:
            continue

        nd = normalized_db[symbol]
        sector = get_sector(symbol)
        group_label = get_sub_sector(symbol)
        config = SUB_SECTOR_CONFIG.get(group_label) or SUB_SECTOR_CONFIG.get(
            sector, SUB_SECTOR_CONFIG["SAN_XUAT_TIEU_DUNG_PHONG_THU"]
        )
        median, _ = get_median_for_symbol(symbol, sector_medians)
        fv = compute_fair_value_zone(symbol, nd, median, config, group_label)

        raw["sector"] = sector
        raw["sub_sector"] = group_label
        raw["bvps"] = round(nd["bvps"], 0)
        raw["fair_value_high"] = fv["fair_high"]
        raw["fair_value_low"] = fv["fair_low"]
        raw["graham_number"] = fv["graham"]
        raw["margin_of_safety_pct"] = fv["mos_pct"]
        raw["fair_value_methods"] = fv["methods"]
        raw["fair_value_rationale"] = fv["rationale"]
        raw["discount_to_fair_pct"] = fv["discount_to_fair_pct"]
        raw["valuation_verdict"] = fv["verdict"]
        raw["valuation_calculated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🆕 Quyết định cuối cùng
        fund_s = raw.get("fundamental_score", 0) or 0
        tech_s = raw.get("technical_score", 0) or 0
        val_s = raw.get("valuation_score", 0) or 0
        total_s = raw.get("total_score", 0) or 0

        fd_label, fd_color, fd_reason = compute_final_decision(
            fund_score=fund_s, tech_score=tech_s, val_score=val_s, total_score=total_s,
            verdict=fv["verdict"], cfo=nd["cfo_latest"], npat=nd["net_profit_ttm"],
            roe=nd["roe"], debt_to_equity=nd["debt_to_equity"],
            discount_to_fair_pct=fv["discount_to_fair_pct"],
            close_price=nd["close_price"], fair_high=fv["fair_high"], fair_low=fv["fair_low"]
        )
        raw["final_decision"] = fd_label
        raw["final_decision_color"] = fd_color
        raw["final_decision_reason"] = fd_reason

        for ai_field in AI_FIELDS:
            if ai_field in raw and not raw.get(ai_field):
                print(f"   ⚠️ Cảnh báo: {symbol} mất trường AI '{ai_field}'")

        raw_db[symbol] = raw
        updated += 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_db, f, ensure_ascii=False, indent=4)

    return updated


# ============================================================
# MAIN
# ============================================================
def main():
    print("🚀 Bộ lọc Quant + Vùng mua + Quyết định cuối cùng (đủ 4 yếu tố)...")

    if not os.path.exists(DATA_FILE):
        print(f"⚠️ Không tìm thấy {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    normalized_db = {s: normalize_stock_data(s, r) for s, r in stock_db.items()}

    print("📊 Đang tính median ngành...")
    sector_medians = compute_sector_medians(normalized_db)
    for sec, m in sector_medians.items():
        print(f"   [{sec:18s}] n={m['n']:2d} | P/E={m['pe']:6.2f} | P/B={m['pb']:5.2f} | ROE={m['roe']:5.1f}%")

    results = []
    for symbol, nd in normalized_db.items():
        sector = get_sector(symbol)
        group_label = get_sub_sector(symbol)
        config = SUB_SECTOR_CONFIG.get(group_label) or SUB_SECTOR_CONFIG.get(
            sector, SUB_SECTOR_CONFIG["SAN_XUAT_TIEU_DUNG_PHONG_THU"]
        )
        median, _ = get_median_for_symbol(symbol, sector_medians)
        res = evaluate_stock(symbol, nd, median, group_label, config)
        if res:
            results.append(res)

    if not results:
        print("⚠️ Không có kết quả.")
        return

    results = sorted(results, key=lambda x: (x.get("total_score", 0), x.get("fundamental_score", 0)), reverse=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✅ Đã tạo: {OUTPUT_JSON}, {OUTPUT_CSV}")

    # ============ BÁO CÁO ============
    print("\n💰 TOP 10 MÃ ĐANG TRONG VÙNG MUA (giá <= fair_low):")
    cheap = [r for r in results if r["valuation_verdict"] == "RẺ - TRONG VÙNG MUA"]
    cheap.sort(key=lambda x: x["discount_to_fair_pct"], reverse=True)
    for r in cheap[:10]:
        print(f"   {r['symbol']:5s} [{r['sub_sector']:14s}] | "
              f"Giá {r['close_price']:>10,.0f} | Mua ≤ {r['fair_value_low']:>10,.0f} | "
              f"CK {r['discount_to_fair_pct']:>5.1f}% | Điểm {r['total_score']}")

    print("\n" + "=" * 70)
    print("🎯 BÁO CÁO QUYẾT ĐỊNH CUỐI CÙNG (Đủ 4: Vùng mua + PTCB + PTKT + Định giá)")
    print("=" * 70)

    decision_groups = [
        ("🎯 MUA MẠNH", "🎯 MUA MẠNH — Đủ 4 yếu tố xuất sắc"),
        ("✅ MUA TÍCH SẢN", "✅ MUA TÍCH SẢN — Đủ 4 yếu tố tốt"),
        ("⚠️ CHỜ VỀ VÙNG MUA", "⚠️ CHỜ VỀ VÙNG MUA — Doanh nghiệp tốt, giá chưa rẻ"),
        ("⏳ CHỜ XÁC NHẬN KỸ THUẬT", "⏳ CHỜ XÁC NHẬN KỸ THUẬT — PTKT yếu"),
        ("⏳ CHỜ ĐỊNH GIÁ TỐT HƠN", "⏳ CHỜ ĐỊNH GIÁ TỐT HƠN — Định giá chưa hấp dẫn"),
        ("❌ TRÁNH", "❌ TRÁNH — Không nên mua"),
        ("⚠️ CẢNH BÁO LỢI NHUẬN ẢO", "⚠️ CẢNH BÁO LỢI NHUẬN ẢO — CFO âm"),
        ("👀 THEO DÕI", "👀 THEO DÕI — Chưa đủ điều kiện"),
    ]

    for key, label in decision_groups:
        group = [r for r in results if r["final_decision"] == key]
        print(f"\n{label} ({len(group)} mã):")
        if group:
            for r in group[:10]:
                print(f"   {r['symbol']:5s} | Giá {r['close_price']:>10,.0f} | "
                      f"PTCB {r['fundamental_score']:>2}/50 | "
                      f"PTKT {r['technical_score']:>2}/20 | "
                      f"Định giá {r['valuation_score']:>2}/30 | "
                      f"Tổng {r['total_score']:>3} | {r['valuation_verdict']}")
        else:
            print("   (Không có mã nào)")

    # ============ GHI VÀO data.json ============
    print("\n💾 Đang ghi các trường vào data.json (không đụng trường AI)...")
    n_updated = update_data_json_with_valuation(normalized_db, sector_medians)
    print(f"   ✅ Đã cập nhật {n_updated} mã với 15 trường định giá + quyết định.")
    print("   🔒 Trường AI được giữ nguyên.")


if __name__ == "__main__":
    main()
