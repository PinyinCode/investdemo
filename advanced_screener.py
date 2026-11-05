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

# Phân nhóm ngành chuẩn chi tiết cho VN100 (7 Nhóm ngành)
SECTOR_MAPPING = {
    "NGAN_HANG": ["ACB","BID","CTG","TCB","MBB","STB","VPB","HDB","VIB","TPB","SHB","SSB","LPB","MSB","OCB","EIB","VCB"],
    "CHUNG_KHOAN": ["SSI","VCI","HCM","VIX","MBS","FTS","BSI","CTS","ORS"],
    "BAT_DONG_SAN": ["VHM","VIC","VRE","NVL","PDR","DIG","NLG","KDH","CEO","DXG","TCH","HDG","KBC","IDC","SZC","BCM","PHR","SJS","VPI"],
    "CONG_NGHE_BAN_LE": ["FPT","MWG","PNJ","FRT","DGW"],
    "DIEN_NUOC_HA_TANG": ["POW","REE","PC1","NT2","GAS","GEG","BWE","TDM"],
    "NGUYEN_VAT_LIEU_CHU_KY": ["HPG","HSG","NKG","DGC","DCM","DPM","GVR","PHR","DHC"],
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": ["VNM","MSN","SAB","VHC","ANV","BVH","PLX","PVD","PVS","BSR","GMD","HAH","PVT","HVN","APH","ASM","DBC","KDC","MSH","PAN","SBT","DRC","CSM","BMP","DHG","CTD","VCG","HHV","GEX"],
}


def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"


def load_bctc_supplement(symbol):
    """Fallback đọc dữ liệu bổ sung từ thư mục bctc_data nếu dữ liệu API hàng ngày bị thiếu"""
    bctc_path = os.path.join(BCTC_DIR, f"{symbol.upper()}.json")
    if os.path.exists(bctc_path):
        try:
            with open(bctc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ============================================================
# 📊 HELPER: TÍNH MEDIAN NGÀNH (DÙNG CHO ĐỊNH GIÁ TƯƠNG QUAN)
# ============================================================
def compute_sector_medians(stock_db):
    """
    Tính median P/E, P/B, PS, ROE của từng ngành từ chính dữ liệu đã có.
    Dùng để định giá tương quan (rẻ/đắt so với chính ngành đó).
    """
    buckets = {}
    for symbol, data in stock_db.items():
        sector = get_sector(symbol)
        pe = data.get("pe", 0) or 0
        pb = data.get("pb", 0) or 0
        ps = data.get("ps", 0) or 0
        roe = data.get("roe", 0) or 0

        # Fallback từ bctc_data
        if pe == 0 or pb == 0:
            sup = load_bctc_supplement(symbol)
            ratios = sup.get("ratios", [])
            if ratios:
                latest = ratios[0]
                pe = pe or (latest.get("PE") or latest.get("PRICE_TO_EARNINGS") or 0)
                pb = pb or (latest.get("PB") or latest.get("PRICE_TO_BOOK") or 0)
                ps = ps or (latest.get("PS") or latest.get("PRICE_TO_SALES") or 0)

        b = buckets.setdefault(sector, {"pe": [], "pb": [], "ps": [], "roe": []})
        if pe > 0: b["pe"].append(pe)
        if pb > 0: b["pb"].append(pb)
        if ps > 0: b["ps"].append(ps)
        if roe != 0: b["roe"].append(roe)

    medians = {}
    for sector, b in buckets.items():
        medians[sector] = {
            "pe": float(np.median(b["pe"])) if b["pe"] else 0.0,
            "pb": float(np.median(b["pb"])) if b["pb"] else 0.0,
            "ps": float(np.median(b["ps"])) if b["ps"] else 0.0,
            "roe": float(np.median(b["roe"])) if b["roe"] else 0.0,
        }
    return medians


# ============================================================
# 💰 CÔNG THỨC TÍNH VÙNG MUA (FAIR VALUE + MARGIN OF SAFETY)
# ============================================================
def compute_fair_value_zone(symbol, data, sector, sector_median):
    """
    Trả về dict:
      fair_low   : giá mua tối đa (đã trừ biên an toàn)
      fair_high  : giá trị hợp lý trung bình
      graham     : Graham Number (chỉ áp dụng phi tài chính)
      methods    : chi tiết từng phương pháp tính
      mos_pct    : biên an toàn áp dụng (%)
      rationale  : diễn giải bằng chữ
    """
    eps = float(data.get("eps", 0) or 0)
    close = float(data.get("close", data.get("close_price", 0)) or 0)
    pb = float(data.get("pb", 0) or 0)
    pe = float(data.get("pe", 0) or 0)
    roe = float(data.get("roe", 0) or 0)
    cfo = float(data.get("cfo_latest", 0) or 0)
    npat = float(data.get("net_profit_ttm", 0) or 0)
    bvps = (close / pb) if pb > 0 and close > 0 else 0.0

    if eps == 0:
        eps = (close / pe) if pe > 0 else 0.0

    methods = {}
    med_pe = sector_median.get("pe") or 12.0
    med_pb = sector_median.get("pb") or 2.0
    med_roe = sector_median.get("roe") or 0.0

    is_financial = sector in ("NGAN_HANG", "CHUNG_KHOAN")

    # ---- Phương pháp 1: P/E hợp lý theo ngành (có thưởng ROE) ----
    roe_bonus = 1.15 if (roe > 0 and roe > med_roe) else 1.0
    cap_pe = 14 if is_financial else 18
    rational_pe = min(med_pe * roe_bonus, cap_pe)
    if eps > 0:
        methods["PE_method"] = round(eps * rational_pe, 0)

    # ---- Phương pháp 2: P/B hợp lý theo ngành ----
    cap_pb = 1.8 if is_financial else 2.5
    rational_pb = min(med_pb, cap_pb)
    if bvps > 0:
        methods["PB_method"] = round(bvps * rational_pb, 0)

    # ---- Phương pháp 3: Graham Number (chỉ phi tài chính) ----
    graham = 0.0
    if not is_financial and eps > 0 and bvps > 0:
        graham = (22.5 * eps * bvps) ** 0.5
        methods["Graham"] = round(graham, 0)

    # ---- Phương pháp 4: CFO boost (chất lượng lợi nhuận thật) ----
    if npat > 0 and cfo > 0 and (cfo / npat) >= 0.8 and eps > 0:
        methods["CFO_boost"] = round(eps * rational_pe * 1.10, 0)

    if not methods:
        return {
            "fair_low": 0, "fair_high": 0, "graham": 0, "methods": {},
            "mos_pct": 0,
            "rationale": "Không đủ dữ liệu định giá (thiếu EPS/giá/PB).",
            "discount_to_fair_pct": 0,
            "verdict": "KHÔNG ĐỦ DỮ LIỆU",
        }

    # ---- Lấy trung vị có trọng số ----
    weights = {"PE_method": 2, "PB_method": 1.5, "Graham": 2, "CFO_boost": 1}
    weighted = []
    for k, v in methods.items():
        weighted.extend([v] * int(weights.get(k, 1) * 2))
    weighted.sort()
    n = len(weighted)
    fair_high = weighted[n // 2] if n % 2 else (weighted[n//2 - 1] + weighted[n//2]) / 2

    # ---- Biên an toàn theo ngành ----
    mos_map = {
        "NGAN_HANG": 0.20,
        "CHUNG_KHOAN": 0.25,
        "BAT_DONG_SAN": 0.30,
        "NGUYEN_VAT_LIEU_CHU_KY": 0.30,
        "CONG_NGHE_BAN_LE": 0.20,
        "DIEN_NUOC_HA_TANG": 0.15,
        "SAN_XUAT_TIEU_DUNG_PHONG_THU": 0.25,
    }
    mos = mos_map.get(sector, 0.25)
    fair_low = fair_high * (1 - mos)

    # ---- So sánh giá hiện tại với vùng mua ----
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
        f"PE_method={methods.get('PE_method', 0):,.0f} (P/E lý tưởng {rational_pe:.1f}x, "
        f"median ngành {med_pe:.1f}x); "
        f"PB_method={methods.get('PB_method', 0):,.0f} (P/B lý tưởng {rational_pb:.1f}x, "
        f"median ngành {med_pb:.1f}x); "
        f"Graham={methods.get('Graham', 0):,.0f}; "
        f"Biên an toàn {mos*100:.0f}% theo ngành {sector}."
    )

    return {
        "fair_low": round(fair_low, 0),
        "fair_high": round(fair_high, 0),
        "graham": round(graham, 0),
        "methods": {k: round(v, 0) for k, v in methods.items()},
        "mos_pct": round(mos * 100, 1),
        "rationale": rationale,
        "discount_to_fair_pct": round(discount_to_fair, 1),
        "verdict": verdict,
    }


# ============================================================
# 🎯 HÀM CHÍNH ĐÁNH GIÁ CỔ PHIẾU
# ============================================================
def evaluate_stock(symbol, data, sector_median=None):
    sector = get_sector(symbol)

    pe = data.get("pe", 0) or 0
    pb = data.get("pb", 0) or 0
    ps = data.get("ps", 0) or 0
    roe = data.get("roe", 0) or 0
    roa = data.get("roa", 0) or 0
    dividend_yield = data.get("dividend_yield", 0) or 0
    close_price = data.get("close", 0) or 0
    eps = data.get("eps", 0) or 0

    cfo_latest = data.get("cfo_latest", 0) or 0
    net_profit_ttm = data.get("net_profit_ttm", 0) or 0
    debt_to_equity = data.get("debt_to_equity", 0) or 0
    gross_margin = data.get("gross_margin", 0) or 0

    if pe == 0 or pb == 0:
        bctc_supp = load_bctc_supplement(symbol)
        ratios_list = bctc_supp.get("ratios", [])
        if ratios_list:
            latest_ratio = ratios_list[0]
            if pe == 0:
                pe = latest_ratio.get("PE") or latest_ratio.get("PRICE_TO_EARNINGS") or 0
            if pb == 0:
                pb = latest_ratio.get("PB") or latest_ratio.get("PRICE_TO_BOOK") or 0
            if ps == 0:
                ps = latest_ratio.get("PS") or latest_ratio.get("PRICE_TO_SALES") or 0

    bctc_history = data.get("bctc_history", [])
    profit_growth_yoy = 0
    credit_growth_yoy = 0
    if bctc_history:
        latest = bctc_history[0]
        profit_growth_yoy = latest.get("profit_growth_yoy", 0) or 0
        credit_growth_yoy = latest.get("credit_growth_yoy", 0) or 0

    # ============ 1. ĐIỂM CƠ BẢN (50 điểm) ============
    fundamental_score = 0
    fund_notes = []

    if sector == "NGAN_HANG":
        if credit_growth_yoy >= 12:
            fundamental_score += 18
            fund_notes.append("Tín dụng mạnh (>=12%)")
        elif credit_growth_yoy >= 8:
            fundamental_score += 10
            fund_notes.append("Tín dụng khá")
        if roe >= 18:
            fundamental_score += 17
            fund_notes.append("ROE xuất sắc (>=18%)")
        elif roe >= 14:
            fundamental_score += 10
            fund_notes.append("ROE tốt (>=14%)")

    elif sector == "CHUNG_KHOAN":
        if profit_growth_yoy >= 20:
            fundamental_score += 20
            fund_notes.append("LN tăng trưởng mạnh (>=20%)")
        elif profit_growth_yoy >= 10:
            fundamental_score += 10
            fund_notes.append("LN hồi phục tốt")
        if roe >= 15:
            fundamental_score += 15
            fund_notes.append("ROE ngành CK cao (>=15%)")
        elif roe >= 10:
            fundamental_score += 8
            fund_notes.append("ROE ổn định")

    elif sector == "BAT_DONG_SAN":
        if profit_growth_yoy >= 10:
            fundamental_score += 15
            fund_notes.append("LN duy trì tăng trưởng")
        if roe >= 12:
            fundamental_score += 20
            fund_notes.append("ROE BĐS đạt chuẩn (>=12%)")
        elif roe > 0:
            fundamental_score += 10
            fund_notes.append("Có lãi dương")

    elif sector == "CONG_NGHE_BAN_LE":
        if profit_growth_yoy >= 20:
            fundamental_score += 18
            fund_notes.append("Tăng trưởng lõi mạnh (>=20%)")
        elif profit_growth_yoy >= 10:
            fundamental_score += 10
            fund_notes.append("Tăng trưởng ổn định")
        if roe >= 18:
            fundamental_score += 17
            fund_notes.append("ROE xuất sắc")
        elif roe >= 12:
            fundamental_score += 10
            fund_notes.append("ROE tốt")

    elif sector == "DIEN_NUOC_HA_TANG":
        if dividend_yield >= 6.0:
            fundamental_score += 20
            fund_notes.append(f"Cổ tức hạ tầng hấp dẫn ({dividend_yield}%)")
        elif dividend_yield > 0:
            fundamental_score += 10
            fund_notes.append(f"Có chia cổ tức ({dividend_yield}%)")
        if roe >= 10:
            fundamental_score += 15
            fund_notes.append("ROE ổn định phòng thủ")
        else:
            fundamental_score += 8

    elif sector == "NGUYEN_VAT_LIEU_CHU_KY":
        if profit_growth_yoy >= 15:
            fundamental_score += 18
            fund_notes.append("Hưởng lợi chu kỳ / LN tăng mạnh")
        elif profit_growth_yoy >= 0:
            fundamental_score += 10
            fund_notes.append("Duy trì nhịp cơ bản")
        if roe >= 12:
            fundamental_score += 17
            fund_notes.append("ROE chu kỳ tốt")
        else:
            fundamental_score += 8

    else:
        if profit_growth_yoy >= 10:
            fundamental_score += 15
            fund_notes.append("LN tăng trưởng tốt")
        elif profit_growth_yoy >= 0:
            fundamental_score += 8
            fund_notes.append("LN ổn định")
        if roe >= 14:
            fundamental_score += 20
            fund_notes.append("ROE sản xuất cao (>=14%)")
        elif roe >= 10:
            fundamental_score += 10
            fund_notes.append("ROE khá")

    if roa >= 5.0:
        fundamental_score += 5
        fund_notes.append(f"ROA rất cao ({roa}%)")
    elif roa >= 2.5:
        fundamental_score += 3
        fund_notes.append(f"ROA tốt ({roa}%)")

    if sector not in ["NGAN_HANG", "CHUNG_KHOAN"]:
        if cfo_latest > 0 and (net_profit_ttm <= 0 or cfo_latest >= net_profit_ttm * 0.8):
            fundamental_score += 5
            fund_notes.append("Dòng tiền kinh doanh (CFO) mạnh mẽ")
        elif cfo_latest < 0:
            fundamental_score -= 5
            fund_notes.append("⚠️ Cảnh báo: CFO âm")
        if 0 < debt_to_equity <= 1.0:
            fundamental_score += 5
            fund_notes.append(f"Cấu trúc tài chính an toàn (D/E: {debt_to_equity})")
        elif debt_to_equity > 2.5:
            fundamental_score -= 5
            fund_notes.append(f"⚠️ Cảnh báo: Đòn bẩy nợ cao (D/E: {debt_to_equity})")
    else:
        if dividend_yield >= 4.0:
            fundamental_score += 5
            fund_notes.append(f"Cổ tức tiền mặt tốt ({dividend_yield}%)")
        else:
            fundamental_score += 5
            fund_notes.append("Ngân hàng tối ưu giữ vốn mở rộng")

    fundamental_score = int(np.clip(fundamental_score, 0, 50))

    # ============ 2. ĐIỂM ĐỊNH GIÁ (30 điểm) ============
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

    # ============ 3. ĐIỂM KỸ THUẬT (20 điểm) ============
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
            print(f"⚠️ Lỗi phân tích kỹ thuật {symbol}: {e}")

    technical_score = int(round((technical_score_raw / 100.0) * 20))
    technical_score = int(np.clip(technical_score, 0, 20))

    total_score = fundamental_score + valuation_score + technical_score

    potential_zone = "THEO DÕI THÊM"
    if total_score >= 75:
        potential_zone = "VÙNG TÍCH SẢN TỐI ƯU (A+)"
    elif total_score >= 60:
        potential_zone = "VÙNG MUA AN TOÀN (B)"

    # ============ 💰 TÍNH VÙNG MUA (DETERMINISTIC) ============
    if sector_median is None:
        sector_median = {"pe": 0, "pb": 0, "ps": 0, "roe": 0}
    fv = compute_fair_value_zone(symbol, data, sector, sector_median)

    return {
        "symbol": symbol,
        "sector": sector,
        "close_price": close_price,
        "pe": pe,
        "pb": pb,
        "ps": ps,
        "roe": roe,
        "roa": roa,
        "eps": eps,
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

        # 💰 VÙNG MUA (deterministic, không phụ thuộc AI)
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
# 🚀 MAIN
# ============================================================
def main():
    print("🚀 Chạy bộ lọc Quant: PTCB (50đ) + Định giá Ngành (30đ) + PTKT (20đ) + Vùng mua (deterministic)...")

    if not os.path.exists(DATA_FILE):
        print(f"⚠️ Không tìm thấy file {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    # 1) Tính median ngành TRƯỚC để định giá tương quan
    print("📊 Đang tính median ngành (P/E, P/B, P/S, ROE)...")
    sector_medians = compute_sector_medians(stock_db)
    for sec, m in sector_medians.items():
        print(f"   [{sec:32s}] P/E={m['pe']:6.2f} | P/B={m['pb']:5.2f} | P/S={m['ps']:5.2f} | ROE={m['roe']:5.1f}%")

    # 2) Đánh giá từng mã với median của ngành nó
    results = []
    for symbol, data in stock_db.items():
        sector = get_sector(symbol)
        median = sector_medians.get(sector, {"pe": 0, "pb": 0, "ps": 0, "roe": 0})
        res = evaluate_stock(symbol, data, sector_median=median)
        if res:
            results.append(res)

    if not results:
        print("⚠️ Không có dữ liệu để xử lý.")
        return

    results = sorted(
        results,
        key=lambda x: (x.get("total_score", 0), x.get("fundamental_score", 0)),
        reverse=True,
    )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n✅ Hoàn tất!")
    print(f"   - {OUTPUT_JSON}")
    print(f"   - {OUTPUT_CSV}")

    # In nhanh top 5 có vùng mua
    print("\n💰 TOP 5 CÓ VÙNG MUA HẤP DẪN NHẤT (giá <= fair_low):")
    cheap = [r for r in results if r["valuation_verdict"] == "RẺ - TRONG VÙNG MUA"]
    cheap.sort(key=lambda x: x["discount_to_fair_pct"], reverse=True)
    for r in cheap[:5]:
        print(f"   {r['symbol']:5s} | Giá {r['close_price']:>9,.0f} | "
              f"Mua <= {r['fair_value_low']:>9,.0f} | "
              f"Fair {r['fair_value_high']:>9,.0f} | "
              f"Chiết khấu {r['discount_to_fair_pct']:>5.1f}% | "
              f"{r['valuation_verdict']}")


if __name__ == "__main__":
    main()
