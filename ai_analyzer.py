import os
import time
import requests
import re
import json
import argparse

SCREENER_FILE = "screener_results.json"
DATA_FILE = "data.json"

ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "").strip()
INPUT_SYMBOLS = os.getenv("INPUT_SYMBOLS", "").strip()
API_URL = "https://ws-8lcqaxwxdv0h9xzy.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"

RESUME_DAYS = 7

SECTOR_MAPPING = {
    "NGAN_HANG": ["ACB","BID","CTG","TCB","MBB","STB","VPB","HDB","VIB","TPB","SHB","SSB","LPB","MSB","OCB","EIB","VCB"],
    "CHUNG_KHOAN": ["SSI","VCI","HCM","VIX","MBS","FTS","BSI","CTS","ORS"],
    "BAT_DONG_SAN": ["VHM","VIC","VRE","NVL","PDR","DIG","NLG","KDH","CEO","DXG","TCH","HDG","KBC","IDC","SZC","BCM","PHR","SJS","VPI"],
    "CONG_NGHE_BAN_LE": ["FPT","MWG","PNJ","FRT","DGW"],
    "DIEN_NUOC_HA_TANG": ["POW","REE","PC1","NT2","GAS","GEG","BWE","TDM"],
    "NGUYEN_VAT_LIEU_CHU_KY": ["HPG","HSG","NKG","DGC","DCM","DPM","GVR","PHR","DHC"],
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": ["VNM","MSN","SAB","VHC","ANV","BVH","PLX","PVD","PVS","BSR","GMD","HAH","PVT","VJC","HVN","APH","ASM","DBC","KDC","MSH","PAN","SBT","DRC","CSM","BMP","DHG","CTD","VCG","HHV","GEX"],
}

SECTOR_NAMES = {
    "NGAN_HANG": "Ngân hàng",
    "CHUNG_KHOAN": "Chứng khoán",
    "BAT_DONG_SAN": "Bất động sản",
    "CONG_NGHE_BAN_LE": "Công nghệ & Bán lẻ",
    "DIEN_NUOC_HA_TANG": "Điện, Nước & Hạ tầng",
    "NGUYEN_VAT_LIEU_CHU_KY": "Vật liệu & Chu kỳ",
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": "Sản xuất & Tiêu dùng",
}

TOP_PER_SECTOR = 5


def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"


def is_recently_analyzed(stock_metrics, days=RESUME_DAYS):
    ts_str = stock_metrics.get("ai_updated_at", "")
    if not ts_str:
        return False
    try:
        ts = time.mktime(time.strptime(ts_str, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return False
    return (time.time() - ts) < days * 24 * 3600


DECISION_TO_RECOMMENDATION = {
    "🎯 MUA MẠNH":                     ("MUA MẠNH", "Tỷ trọng 20-30% — Giải ngân toàn bộ hoặc theo 2-3 đợt"),
    "✅ MUA TÍCH SẢN":                  ("MUA TÍCH SẢN", "Tỷ trọng 10-15% — Giải ngân từng phần (DCA)"),
    "⚠️ CHỜ VỀ VÙNG MUA":               ("CHỜ VỀ VÙNG MUA", "Tỷ trọng 0% — Chờ giá về fair_low mới mua"),
    "⏳ CHỜ XÁC NHẬN KỸ THUẬT":         ("CHỜ XÁC NHẬN KỸ THUẬT", "Tỷ trọng 0% — Chờ breakout có volume xác nhận"),
    "⏳ CHỜ ĐỊNH GIÁ TỐT HƠN":          ("CHỜ ĐỊNH GIÁ TỐT HƠN", "Tỷ trọng 0% — Định giá chưa hấp dẫn"),
    "❌ TRÁNH":                         ("TRÁNH", "Tỷ trọng 0% — Không mua"),
    "⚠️ CẢNH BÁO LỢI NHUẬN ẢO":         ("CẢNH BÁO", "Tỷ trọng 0% — Lợi nhuận không có tiền mặt thật"),
    "👀 THEO DÕI":                      ("NẮM GIỮ / THEO DÕI", "Tỷ trọng 0% — Chưa đủ điều kiện mua"),
}


# ============================================================
# 📝 TEMPLATE FALLBACK — KHÔNG CẦN AI VẪN CÓ BÁO CÁO
# ============================================================
def build_fallback_narrative(symbol, stock_metrics, screener_item, sector):
    close = float(stock_metrics.get("close", stock_metrics.get("close_price", 0)) or 0)
    pe = float(stock_metrics.get("pe", 0) or 0)
    pb = float(stock_metrics.get("pb", 0) or 0)
    roe = float(stock_metrics.get("roe", 0) or 0)
    roa = float(stock_metrics.get("roa", 0) or 0)
    eps = float(stock_metrics.get("eps", 0) or 0)
    cfo = float(stock_metrics.get("cfo_latest", 0) or 0)
    npat = float(stock_metrics.get("net_profit_ttm", 0) or 0)
    de = float(stock_metrics.get("debt_to_equity", 0) or 0)
    gm = float(stock_metrics.get("gross_margin", 0) or 0)
    div_yield = float(stock_metrics.get("dividend_yield", 0) or 0)

    fair_low = float(stock_metrics.get("fair_value_low", 0) or 0)
    fair_high = float(stock_metrics.get("fair_value_high", 0) or 0)
    discount_pct = float(stock_metrics.get("discount_to_fair_pct", 0) or 0)
    verdict = stock_metrics.get("valuation_verdict", "CHƯA TÍNH")
    mos_pct = float(stock_metrics.get("margin_of_safety_pct", 0) or 0)
    
    # Đọc điểm số từ screener_item (file screener_results.json - luôn chuẩn xác)
    fund_score = screener_item.get("fundamental_score", 0)
    val_score = screener_item.get("valuation_score", 0)
    tech_score = screener_item.get("technical_score", 0)
    total_score = screener_item.get("total_score", 0)
    growth_yoy = float(screener_item.get("profit_growth_yoy", 0) or 0)

    # ĐỌC TRỰC TIẾP QUYẾT ĐỊNH TỪ SCREENER_RESULTS.JSON
    final_decision = screener_item.get("final_decision", "CHƯA XÁC ĐỊNH")

    sector_name = SECTOR_NAMES.get(sector, sector)
    is_bank_or_sec = sector in ("NGAN_HANG", "CHUNG_KHOAN")

    # BCTC
    bctc_parts = [
        f"Chỉ số sinh lời: ROE đạt {roe:.1f}%, ROA {roa:.1f}% — "
        + ("vượt trội so với mặt bằng chung ngành." if roe >= 15 else "ở mức trung bình ngành." if roe >= 10 else "còn khá thấp, cần cải thiện.")
    ]
    if is_bank_or_sec:
        bctc_parts.append(
            f"P/E {pe:.2f}x và P/B {pb:.2f}x phản ánh mức định giá của một định chế tài chính. "
            f"Với đặc thù ngân hàng, D/E {de:.2f} là bản chất từ tiền gửi khách hàng, không phải dấu hiệu rủi ro."
        )
    else:
        bctc_parts.append(f"Định giá P/E {pe:.2f}x và P/B {pb:.2f}x.")
        if gm > 0:
            bctc_parts.append(f"Biên lợi nhuận gộp {gm:.1f}% duy trì ở mức tốt.")

    if npat > 0 and cfo != 0:
        cfo_ratio = cfo / npat
        if cfo_ratio >= 1.0:
            bctc_parts.append(f"Chất lượng lợi nhuận tốt với CFO {cfo:,.0f} tỷ ≥ LNST {npat:,.0f} tỷ (CFO/LNST = {cfo_ratio:.2f}x) — lợi nhuận thật, có tiền mặt.")
        elif cfo_ratio >= 0.5:
            bctc_parts.append(f"CFO {cfo:,.0f} tỷ so với LNST {npat:,.0f} tỷ (CFO/LNST = {cfo_ratio:.2f}x) — chấp nhận được.")
        else:
            bctc_parts.append(f"⚠️ Cảnh báo: CFO/LNST chỉ {cfo_ratio:.2f}x — lợi nhuận kém tiền mặt, cần theo dõi khoản phải thu.")

    if not is_bank_or_sec and de > 2.5:
        bctc_parts.append(f"⚠️ Đòn bẩy cao D/E {de:.2f} cần được theo dõi.")

    bctc_parts.append(f"EPS đạt {eps:,.0f} VNĐ" + (f", cổ tức {div_yield}%/năm — thu nhập thụ động hấp dẫn." if div_yield > 0 else "."))
    bctc = " ".join(bctc_parts)

    # Catalyst
    moat_map = {
        "NGAN_HANG": "tệp khách hàng bán lẻ trung thành, chi phí vốn thấp nhờ mạng lưới huy động dân cư sâu rộng và hệ thống quản trị rủi ro top đầu ngành",
        "CHUNG_KHOAN": "thị phần môi giới ổn định, quan hệ với nhà đầu tư tổ chức và năng lực tự doanh có kỷ luật",
        "BAT_DONG_SAN": "quỹ đất sạch tại vị trí đắc địa, pháp lý dự án hoàn thiện và thương hiệu chủ đầu tư uy tín",
        "CONG_NGHE_BAN_LE": "thương hiệu mạnh, chuỗi cung ứng tối ưu và tệp khách hàng trung thành",
        "DIEN_NUOC_HA_TANG": "vị thế độc quyền tự nhiên, hợp đồng dài hạn và dòng tiền ổn định",
        "NGUYEN_VAT_LIEU_CHU_KY": "quy mô sản xuất lớn, chi phí biên thấp và vị thế dẫn đầu ngành",
        "SAN_XUAT_TIEU_DUNG_PHONG_THU": "thương hiệu quốc dân, mạng lưới phân phối rộng khắp và thị phần dẫn đầu",
    }
    moat = moat_map.get(sector, "lợi thế cạnh tranh dài hạn của doanh nghiệp")
    catalyst_parts = [f"Lợi thế cạnh tranh cốt lõi (Economic Moat) nằm ở {moat}."]
    if growth_yoy > 15:
        catalyst_parts.append(f"Động lực tăng trưởng mạnh: LNST tăng {growth_yoy:.1f}% YoY, kỳ vọng duy trì đà tăng trong 2-3 năm tới.")
    elif growth_yoy > 0:
        catalyst_parts.append(f"Tăng trưởng ổn định với LNST tăng {growth_yoy:.1f}% YoY.")
    else:
        catalyst_parts.append(f"Tăng trưởng LNST hiện ở mức {growth_yoy:.1f}% YoY, cần theo dõi thêm.")
    catalyst = " ".join(catalyst_parts)

    # Risks
    risk_map = {
        "NGAN_HANG": f"Rủi ro nợ xấu gia tăng từ bất động sản và SME, đặc biệt khi D/E hiện ở mức {de:.2f}. Áp lực thu hẹp NIM khi lãi suất cho vay giảm. Rủi ro thanh khoản cục bộ trên thị trường trái phiếu.",
        "CHUNG_KHOAN": f"Rủi ro thanh khoản thị trường suy giảm làm giảm doanh thu môi giới và margin. Rủi ro danh mục tự doanh khi thị trường đảo chiều. Rủi ro ROE {roe:.1f}% không duy trì được khi chu kỳ xuống.",
        "BAT_DONG_SAN": "Rủi ro pháp lý dự án, tiến độ bàn giao chậm. Rủi ro đòn bẩy nợ cao nếu D/E vượt ngưỡng an toàn. Rủi ro thanh khoản thị trường BĐS đóng băng.",
        "CONG_NGHE_BAN_LE": f"Rủi ro tăng trưởng chậm lại khi thị trường bão hòa. Rủi ro biên lợi nhuận gộp {gm:.1f}% bị thu hẹp do cạnh tranh. Rủi ro hàng tồn kho tăng cao.",
        "DIEN_NUOC_HA_TANG": "Rủi ro chính sách giá điện/nước thay đổi. Rủi ro chi phí vốn tăng khi lãi suất lên. Rủi ro thời tiết khắc nghiệt ảnh hưởng sản lượng.",
        "NGUYEN_VAT_LIEU_CHU_KY": f"Rủi ro giá hàng hóa đảo chiều làm biên gộp {gm:.1f}% co lại. Bẫy P/E {pe:.2f}x thấp tại đỉnh lợi nhuận chu kỳ. Rủi ro tồn kho cao nếu giá giảm.",
        "SAN_XUAT_TIEU_DUNG_PHONG_THU": f"Rủi ro cạnh tranh từ hàng nhập khẩu và thương hiệu mới. Rủi ro biên gộp {gm:.1f}% bị ép bởi chi phí nguyên liệu. Rủi ro sức mua tiêu dùng suy yếu.",
    }
    risks = risk_map.get(sector, f"Rủi ro chung của ngành {sector_name} và biến động thị trường.")

    # Outlook (TẬP TRUNG VÀO BIÊN AN TOÀN)
    if verdict == "RẺ - TRONG VÙNG MUA":
        outlook = (
            f"Giá hiện tại {close:,.0f} VNĐ nằm dưới vùng mua an toàn {fair_low:,.0f} VNĐ, "
            f"tạo biên an toàn thực {discount_pct:.1f}% (MoS {mos_pct:.0f}%). "
            f"Hệ thống xác định Verdict: {verdict}. "
            f"Với P/E {pe:.2f}x và P/B {pb:.2f}x, đây là vùng định giá hấp dẫn cho tích sản dài hạn. "
            f"Quyết định hệ thống: {final_decision}."
        )
    elif verdict == "HỢP LÝ - CHỜ ĐIỀU CHỈNH":
        outlook = (
            f"Giá {close:,.0f} VNĐ nằm giữa vùng mua {fair_low:,.0f} và fair value {fair_high:,.0f} VNĐ. "
            f"Định giá hợp lý nhưng chưa có biên an toàn. "
            f"Verdict: {verdict}. Quyết định hệ thống: {final_decision}. "
            f"Nếu giá điều chỉnh về {fair_low:,.0f} VNĐ sẽ là vùng mua hấp dẫn."
        )
    elif verdict == "HƠI ĐẮT - KHÔNG MUA":
        outlook = (
            f"Giá {close:,.0f} VNĐ đã vượt fair value {fair_high:,.0f} VNĐ. "
            f"Định giá hiện tại chưa hấp dẫn cho tích sản mới. "
            f"Verdict: {verdict}. Quyết định hệ thống: {final_decision}. "
            f"Chờ giá điều chỉnh về {fair_low:,.0f} VNĐ mới nên giải ngân."
        )
    elif verdict == "ĐẮT - TRÁNH":
        outlook = (
            f"Giá {close:,.0f} VNĐ đã vượt xa fair value {fair_high:,.0f} VNĐ. "
            f"Định giá đắt rõ rệt, không phù hợp đầu tư giá trị. "
            f"Verdict: {verdict}. Quyết định hệ thống: {final_decision}."
        )
    else:
        outlook = f"Chưa đủ dữ liệu định giá. Verdict: {verdict}. Quyết định: {final_decision}."

    rec_text, rec_weight = DECISION_TO_RECOMMENDATION.get(
        final_decision, ("NẮM GIỮ / THEO DÕI", "Tỷ trọng 0%")
    )
    recommendation = f"{rec_text} — {rec_weight}"

    price_zone = (
        f"Vùng mua: {fair_low:,.0f} — {fair_high:,.0f} | "
        f"Giá hiện tại: {close:,.0f} | Verdict: {verdict}"
    )

    # Vĩ mô (TẬP TRUNG VÀO CHU KỲ NGÀNH)
    macro_map = {
        "NGAN_HANG": "Chu kỳ tín dụng đang phục hồi khi lãi suất huy động duy trì thấp. NIM có thể chịu áp lực khi Chính phủ thúc đẩy giảm lãi vay. Luật Các TCTD sửa đổi tạo lợi thế cho ngân hàng quản trị minh bạch. Rủi ro nợ xấu BĐS còn hiện hữu trong ngắn hạn.",
        "CHUNG_KHOAN": "Thanh khoản thị trường là yếu tố quyết định doanh thu ngành. Chính sách nâng hạng thị trường (FTSE) tạo catalyst trung hạn. Chu kỳ lãi suất thấp hỗ trợ dòng tiền vào chứng khoán.",
        "BAT_DONG_SAN": "Pháp lý BĐS (Luật Đất đai, Luật Nhà ở) đang dần tháo gỡ. Tín dụng BĐS hồi phục nhưng chậm. Chu kỳ phục hồi phụ thuộc vào niềm tin người mua và thanh khoản ngân hàng.",
        "CONG_NGHE_BAN_LE": "Sức mua tiêu dùng nội địa phục hồi dần. Xu hướng chuyển đổi số và thương mại điện tử tạo dư địa tăng trưởng. Cạnh tranh từ hàng nhập khẩu giá rẻ vẫn gay gắt.",
        "DIEN_NUOC_HA_TANG": "Nhu cầu điện tăng theo tăng trưởng GDP. Chính sách phát triển năng lượng tái tạo tạo cơ hội. Rủi ro chính sách giá điện và thủy văn bất thường.",
        "NGUYEN_VAT_LIEU_CHU_KY": "Chu kỳ giá hàng hóa phụ thuộc vào kinh tế Trung Quốc và chính sách bảo hộ thương mại toàn cầu. Cần theo dõi tồn kho và giá nguyên liệu đầu vào.",
        "SAN_XUAT_TIEU_DUNG_PHONG_THU": "Tiêu dùng nội địa phục hồi nhưng chậm. Cạnh tranh từ hàng nhập khẩu và áp lực biên lợi nhuận từ chi phí nguyên liệu. Cơ hội từ xuất khẩu nếu tỷ giá thuận lợi.",
    }
    macro_view = macro_map.get(sector, f"Ngành {sector_name} chịu ảnh hưởng chung từ chu kỳ kinh tế vĩ mô.")

    return {
        "bctc": bctc,
        "catalyst": catalyst,
        "risks": risks,
        "valuation_verdict": verdict,
        "outlook": outlook,
        "recommendation": recommendation,
        "price_zone": price_zone,
        "macro_view": macro_view,
        "_source": "TEMPLATE_FALLBACK",
    }


def get_sector_guidance(sector):
    guidance = {
        "NGAN_HANG": "ĐẶC THÙ NGÂN HÀNG: D/E cao là bản chất vì nợ = tiền gửi KH. CFO âm khi mở rộng tín dụng là bình thường. Trọng tâm: ROE, ROA, tăng trưởng tín dụng, NIM.",
        "CHUNG_KHOAN": "ĐẶC THÙ CHỨNG KHOÁN: Doanh thu phụ thuộc thanh khoản TT + margin + tự doanh. Trọng tâm: ROE, tăng trưởng LNST YoY.",
        "BAT_DONG_SAN": "ĐẶC THÙ BẤT ĐỘNG SẢN: Doanh thu ghi nhận theo tiến độ dự án. Trọng tâm: P/B, ROE, dòng tiền người mua trả trước.",
        "CONG_NGHE_BAN_LE": "ĐẶC THÙ CÔNG NGHỆ/BÁN LẺ: Tăng trưởng doanh thu là ưu tiên số 1. Trọng tâm: ROE, biên gộp, tăng trưởng LNST.",
        "DIEN_NUOC_HA_TANG": "ĐẶC THÙ TIỆN ÍCH: Khấu hao lớn nhưng CFO ổn định. Trọng tâm: ROE, cổ tức tiền mặt, CFO.",
        "NGUYEN_VAT_LIEU_CHU_KY": "ĐẶC THÙ VẬT LIỆU CHU KỲ: Cẩn thận bẫy P/E thấp tại đỉnh chu kỳ. Trọng tâm: P/B, ROE, biên gộp.",
        "SAN_XUAT_TIEU_DUNG_PHONG_THU": "ĐẶC THÙ SẢN XUẤT/TIÊU DÙNG: Đánh giá thương hiệu, thị phần. Trọng tâm: ROE, biên gộp, CFO/LNST.",
    }
    return guidance.get(sector, guidance["SAN_XUAT_TIEU_DUNG_PHONG_THU"])


def build_verified_facts(symbol, stock_metrics, screener_item, sector):
    close = float(stock_metrics.get("close", stock_metrics.get("close_price", 0)) or 0)
    pe = float(stock_metrics.get("pe", 0) or 0)
    pb = float(stock_metrics.get("pb", 0) or 0)
    ps = float(stock_metrics.get("ps", 0) or 0)
    roe = float(stock_metrics.get("roe", 0) or 0)
    roa = float(stock_metrics.get("roa", 0) or 0)
    eps = float(stock_metrics.get("eps", 0) or 0)
    bvps = float(stock_metrics.get("bvps", 0) or 0)
    div_yield = float(stock_metrics.get("dividend_yield", 0) or 0)
    cfo = float(stock_metrics.get("cfo_latest", 0) or 0)
    npat = float(stock_metrics.get("net_profit_ttm", 0) or 0)
    de = float(stock_metrics.get("debt_to_equity", 0) or 0)
    gm = float(stock_metrics.get("gross_margin", 0) or 0)

    fair_low = float(stock_metrics.get("fair_value_low", 0) or 0)
    fair_high = float(stock_metrics.get("fair_value_high", 0) or 0)
    graham = float(stock_metrics.get("graham_number", 0) or 0)
    mos_pct = float(stock_metrics.get("margin_of_safety_pct", 0) or 0)
    discount_pct = float(stock_metrics.get("discount_to_fair_pct", 0) or 0)
    verdict = stock_metrics.get("valuation_verdict", "CHƯA TÍNH")
    rationale = stock_metrics.get("fair_value_rationale", "")
    methods = stock_metrics.get("fair_value_methods", {})
    sub_sector = stock_metrics.get("sub_sector", sector)
    
    # ĐỌC TỪ SCREENER_RESULTS.JSON (Chuẩn xác nhất)
    final_decision = screener_item.get("final_decision", "CHƯA XÁC ĐỊNH")
    final_reason = screener_item.get("final_decision_reason", "")

    growth_yoy = float(screener_item.get("profit_growth_yoy", 0) or 0)
    total_score = screener_item.get("total_score", 0)
    fund_score = screener_item.get("fundamental_score", 0)
    val_score = screener_item.get("valuation_score", 0)
    tech_score = screener_item.get("technical_score", 0)
    fund_notes = screener_item.get("fundamental_notes", "")
    potential_zone = screener_item.get("potential_zone", "")
    technical_status = screener_item.get("technical_status", "")
    pattern = screener_item.get("pattern", "")

    cfo_quality = ""
    if npat > 0 and cfo != 0:
        ratio = cfo / npat
        cfo_quality = f" | CFO/LNST = {ratio:.2f}x"
        if ratio >= 1.0: cfo_quality += " (lợi nhuận thật)"
        elif ratio >= 0.8: cfo_quality += " (chất lượng tốt)"
        elif ratio >= 0.5: cfo_quality += " (chấp nhận được)"
        elif ratio > 0: cfo_quality += " (cần lưu ý)"
        else: cfo_quality += " (⚠️ CFO âm)"

    fair_position = ""
    if fair_low > 0 and close > 0:
        if close <= fair_low:
            fair_position = f"✅ ĐANG TRONG VÙNG MUA (thấp hơn fair_low {discount_pct:.1f}%)"
        elif close <= fair_high:
            fair_position = f"⚖️ Giá hợp lý, chờ điều chỉnh về fair_low {fair_low:,.0f}"
        elif close <= fair_high * 1.2:
            fair_position = f"⚠️ HƠI ĐẮT (cao hơn fair_high {((close-fair_high)/fair_high*100):.1f}%)"
        else:
            fair_position = f"❌ ĐẮT (cao hơn fair_high {((close-fair_high)/fair_high*100):.1f}%)"

    lines = [
        f"=== MÃ {symbol} — NGÀNH {sector} — SUB-SECTOR {sub_sector} ===",
        "",
        "[0] 🎯 QUYẾT ĐỊNH CUỐI CÙNG CỦA HỆ THỐNG (BẮT BUỘC TUÂN THỦ)",
        f"  → {final_decision}",
        f"  Lý do hệ thống: {final_reason}",
        f"  Cơ sở: Vùng mua + PTCB {fund_score}/50 + PTKT {tech_score}/20 + Định giá {val_score}/30 = Tổng {total_score}/100",
        "",
        "[1] GIÁ & ĐỊNH GIÁ HIỆN TẠI",
        f"  - Giá: {close:,.0f} VNĐ",
        f"  - P/E = {pe:.2f}x | P/B = {pb:.2f}x | P/S = {ps:.2f}x",
        f"  - EPS = {eps:,.0f} VNĐ | BVPS = {bvps:,.0f} VNĐ",
        f"  - Cổ tức: {div_yield}%/năm",
        "",
        "[2] VÙNG MUA (DETERMINISTIC)",
        f"  - Fair value: {fair_high:,.0f} VNĐ",
        f"  - Vùng mua (fair_low): {fair_low:,.0f} VNĐ",
        f"  - Biên an toàn: {mos_pct:.1f}%",
        f"  - Graham Number: {graham:,.0f} VNĐ" if graham > 0 else "  - Graham Number: N/A (tài chính)",
        f"  - Chi tiết: {json.dumps(methods, ensure_ascii=False)}",
        f"  - Vị thế giá: {fair_position}",
        f"  - Verdict: {verdict}",
        f"  - Chiết khấu so với fair_low: {discount_pct:.1f}%",
        "",
        "[3] HIỆU QUẢ SINH LỜI & CHẤT LƯỢNG",
        f"  - ROE = {roe}% | ROA = {roa}%",
        f"  - LN TTM = {npat:,.0f} Tỷ | CFO = {cfo:,.0f} Tỷ{cfo_quality}",
        f"  - D/E = {de:.2f} | Biên gộp = {gm}%",
        f"  - Tăng trưởng LNST YoY = {growth_yoy}%",
        "",
        "[4] ĐIỂM SỐ HỆ THỐNG",
        f"  - Tổng: {total_score}/100 (Cơ bản {fund_score}/50, Định giá {val_score}/30, Kỹ thuật {tech_score}/20)",
        f"  - Ghi chú: {fund_notes}",
        f"  - Vùng tiềm năng: {potential_zone}",
        f"  - Kỹ thuật: {technical_status} | Mẫu hình: {pattern}",
    ]
    return "\n".join(lines)


def call_ai_api(symbol, stock_metrics, screener_item, sector):
    """Gọi AI, trả về dict hoặc None nếu lỗi."""
    verified_facts = build_verified_facts(symbol, stock_metrics, screener_item, sector)
    sector_guidance = get_sector_guidance(sector)

    fair_low = float(stock_metrics.get("fair_value_low", 0) or 0)
    fair_high = float(stock_metrics.get("fair_value_high", 0) or 0)
    verdict = stock_metrics.get("valuation_verdict", "CHƯA TÍNH")
    discount_pct = float(stock_metrics.get("discount_to_fair_pct", 0) or 0)
    close_price = float(stock_metrics.get("close", stock_metrics.get("close_price", 0)) or 0)
    
    # Lấy từ screener_item
    final_decision = screener_item.get("final_decision", "CHƯA XÁC ĐỊNH")
    final_reason = screener_item.get("final_decision_reason", "")

    rec_text, rec_weight = DECISION_TO_RECOMMENDATION.get(
        final_decision, ("NẮM GIỮ / THEO DÕI", "Tỷ trọng 0%")
    )

    prompt = f"""Bạn là Chuyên gia Phân tích Đầu tư Giá trị (Value Investing) với 20 năm kinh nghiệm tại các quỹ lớn ở Việt Nam.

NHIỆM VỤ: Diễn giải dữ liệu đã tính sẵn cho mã {symbol}. KHÔNG được bịa số liệu. Mọi con số phải TRÍCH DẪN TRỰC TIẾP từ khối DỮ KIỆN bên dưới.

--- DỮ KIỆN ĐÃ KIỂM CHỨNG ---
{verified_facts}

--- HƯỚNG DẪN THEO NGÀNH ---
{sector_guidance}

--- QUY TẮC BẮT BUỘC ---
1. MỌI nhận định phải có SỐ CỤ THỂ từ dữ kiện.
2. VỀ VÙNG MUA: PHẢI dùng đúng 2 con số: fair value {fair_high:,.0f}, vùng mua {fair_low:,.0f}.
3. VỀ KHUYẾN NGHỊ: Hệ thống đã tính → "{final_decision}". BẠN PHẢI trả về recommendation = "{rec_text}" và weight = "{rec_weight}". 
TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ ĐỔI SANG CHỮ "TRÁNH" HAY BẤT KỲ TỪ NÀO KHÁC.
4. VỀ "ĐỊNH GIÁ & HÀNH ĐỘNG GIÁ" (outlook): Phải làm nổi bật "Biên an toàn" (Margin of Safety). Nếu giá đang trong vùng mua, phải kết luận rõ đây là cơ hội. Nếu giá đắt, phải nói rõ rủi ro.
5. VỀ "VĨ MÔ & SÓNG NGÀNH" (macro_view): Phân tích dựa trên chu kỳ giá hàng hóa (đối với ngành Vật liệu/Phân bón/Hóa chất/Thép) hoặc chính sách vĩ mô (đối với Ngân hàng/BĐS). KHÔNG nói chung chung về VN-Index.

--- ĐỊNH DẠNG: JSON THUẦN TÚY (KHÔNG ```json) ---
{{
  "bctc": "6-8 câu phân tích BCTC, trích số: ROE={stock_metrics.get('roe',0)}%, ROA={stock_metrics.get('roa',0)}%, P/E={stock_metrics.get('pe',0)}, P/B={stock_metrics.get('pb',0)}, CFO/LNST, D/E={stock_metrics.get('debt_to_equity',0)}. Kết luận lợi nhuận thật/ảo.",
  "catalyst": "3-4 câu. Economic Moat cụ thể + động lực tăng trưởng 2-3 năm.",
  "risks": "3 câu. Rủi ro trọng yếu nhất phù hợp ngành.",
  "valuation_verdict": "Copy nguyên văn: '{verdict}'",
  "outlook": "4-5 câu. So sánh giá {close_price:,.0f} với vùng mua {fair_low:,.0f}-{fair_high:,.0f}. Giải thích quyết định '{final_decision}'. Nhấn mạnh biên an toàn {discount_pct:.1f}%.",
  "recommendation": "BẮT BUỘC: '{rec_text}' — {rec_weight}",
  "price_zone": "BẮT BUỘC: 'Vùng mua: {fair_low:,.0f} — {fair_high:,.0f} | Giá hiện tại: {close_price:,.0f} | Verdict: {verdict}'",
  "macro_view": "4-5 câu. Phân tích chu kỳ hàng hóa hoặc vĩ mô tác động trực tiếp đến doanh nghiệp."
}}"""

    headers = {"Authorization": f"Bearer {ALIBABA_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "qwen3.7-max",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15,
    }

    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                content = re.sub(r"^```json\s*", "", content)
                content = re.sub(r"^```\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                parsed_data = json.loads(content)

                # Chuẩn hóa price_zone
                raw_pz = parsed_data.get("price_zone", "")
                if isinstance(raw_pz, dict):
                    parsed_data["price_zone"] = " | ".join([f"{k}: {v}" for k, v in raw_pz.items()])
                elif isinstance(raw_pz, list):
                    parsed_data["price_zone"] = " - ".join([str(i) for i in raw_pz])
                else:
                    parsed_data["price_zone"] = str(raw_pz)

                # Post-check price_zone
                if fair_low > 0:
                    pz_text = parsed_data["price_zone"]
                    numbers_in_pz = re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d{4,}", pz_text)
                    allowed = {f"{int(fair_low):,}", f"{int(fair_high):,}", f"{int(close_price):,}"}
                    for num in numbers_in_pz:
                        if num not in allowed and num.replace(",", "").replace(".", "") not in [str(int(fair_low)), str(int(fair_high)), str(int(close_price))]:
                            print(f"  ⚠️ [{symbol}] AI bịa số trong price_zone: {num} → Ghi đè")
                            parsed_data["price_zone"] = (
                                f"Vùng mua: {fair_low:,.0f} — {fair_high:,.0f} | "
                                f"Giá hiện tại: {close_price:,.0f} | Verdict: {verdict}"
                            )
                            break

                # Post-check recommendation
                ai_rec = parsed_data.get("recommendation", "").upper()
                expected_rec = rec_text.upper()
                if expected_rec not in ai_rec:
                    print(f"  ⚠️ [{symbol}] AI tự đổi khuyến nghị → Ghi đè: '{rec_text}'")
                    parsed_data["recommendation"] = f"{rec_text} — {rec_weight}"

                parsed_data["_source"] = "AI"
                return parsed_data
            else:
                print(f"[{symbol}] Lỗi HTTP {response.status_code}")
                break
        except requests.exceptions.Timeout:
            print(f"[{symbol}] ⏳ Timeout {attempt + 1}/3, thử lại...")
            time.sleep(3)
        except Exception as e:
            print(f"[{symbol}] Lỗi AI: {e}")
            break

    return None


def analyze_stock(symbol, stock_metrics, screener_item, sector, use_ai=True):
    """
    Hàm dispatch: gọi AI nếu use_ai=True và có API key, ngược lại dùng template.
    """
    if use_ai and ALIBABA_API_KEY:
        result = call_ai_api(symbol, stock_metrics, screener_item, sector)
        if result is not None:
            return result
        print(f"  → AI lỗi, chuyển sang template fallback cho {symbol}")

    # Fallback: template (không cần AI)
    return build_fallback_narrative(symbol, stock_metrics, screener_item, sector)


def build_target_lists(screener_map):
    industry_groups = {}
    for symbol, item in screener_map.items():
        sector = get_sector(symbol)
        item['sector'] = sector
        industry_groups.setdefault(sector, []).append(item)

    top_symbols = {}
    for sector, items in industry_groups.items():
        # 🆕 TỐI ƯU: Ưu tiên chọn mã có Tổng điểm cao nhất (bao gồm cả Định giá & Kỹ thuật), sau đó đến Điểm cơ bản và Chiết khấu
        items_sorted = sorted(
            items,
            key=lambda x: (
                x.get('total_score', 0),          # Ưu tiên 1: Điểm tổng (thể hiện toàn diện)
                x.get('fundamental_score', 0),    # Ưu tiên 2: Nền tảng doanh nghiệp
                x.get('discount_to_fair_pct', 0)  # Ưu tiên 3: Mức độ rẻ so với giá trị thực
            ),
            reverse=True
        )
        for itm in items_sorted[:TOP_PER_SECTOR]:
            top_symbols[itm['symbol']] = sector
        print(f"📌 Nhóm ngành [{sector}] - Top {TOP_PER_SECTOR}: {[i['symbol'] for i in items_sorted[:TOP_PER_SECTOR]]}")

    remaining_symbols = {}
    for symbol, item in screener_map.items():
        if symbol not in top_symbols:
            remaining_symbols[symbol] = get_sector(symbol)

    return top_symbols, remaining_symbols


def save_db(stock_db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)


def run_group(symbols_dict, label, stock_db, screener_map, sleep_time, use_ai=True):
    if not symbols_dict:
        print(f"⚠️ Nhóm [{label}] rỗng, bỏ qua.")
        return 0

    symbols_sorted = sorted(symbols_dict.keys())
    total = len(symbols_sorted)
    count = 0
    source_label = "AI" if (use_ai and ALIBABA_API_KEY) else "TEMPLATE"

    print(f"\n🚀 Nhóm [{label}]: {total} mã | Nguồn: {source_label}")
    print(f"   Danh sách: {symbols_sorted}\n")

    for idx, symbol in enumerate(symbols_sorted, 1):
        sector = symbols_dict[symbol]
        if symbol not in stock_db:
            stock_db[symbol] = {}
        if symbol not in screener_map:
            continue

        stock_metrics = stock_db[symbol]
        screener_item = screener_map[symbol]

        if float(stock_metrics.get("fair_value_low", 0) or 0) == 0:
            print(f"[{idx}/{total}] ⚠️ [{sector}] {symbol} — CHƯA CÓ VÙNG MUA. Chạy screener.py trước. Bỏ qua.")
            continue

        if not screener_item.get("final_decision"):
            print(f"[{idx}/{total}] ⚠️ [{sector}] {symbol} — Thiếu final_decision. Chạy screener.py để cập nhật.")
            continue

        final_dec = screener_item.get('final_decision', '?')
        print(f"[{idx}/{total}] 🔍 [{sector}] {symbol} | {final_dec}")

        ai_result = analyze_stock(symbol, stock_metrics, screener_item, sector, use_ai=use_ai)

        if ai_result:
            stock_metrics["bctc"] = ai_result.get("bctc", "")
            stock_metrics["catalyst"] = ai_result.get("catalyst", "")
            stock_metrics["risks"] = ai_result.get("risks", "")
            stock_metrics["outlook"] = ai_result.get("outlook", "")
            stock_metrics["ai_recommendation"] = ai_result.get("recommendation", "")
            stock_metrics["ai_price_zone"] = ai_result.get("price_zone", "")
            stock_metrics["macro_view"] = ai_result.get("macro_view", "")
            stock_metrics["ai_source"] = ai_result.get("_source", source_label)
            stock_metrics["ai_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            count += 1
            src = ai_result.get("_source", source_label)
            print(f"  -> ✅ OK ({count}/{total}) [{src}]")
        else:
            print(f"  -> ❌ Lỗi")

        save_db(stock_db)
        # Nếu dùng template không cần sleep (không bị rate limit)
        if use_ai and ALIBABA_API_KEY:
            time.sleep(sleep_time)

    return count


def main():
    parser = argparse.ArgumentParser(description="Phân tích AI + Template fallback cho cổ phiếu")
    parser.add_argument("--mode", choices=["top", "rest", "all"], default="top",
                        help="top: top mỗi ngành; rest: chia batch; all: cả hai")
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--total-batches", type=int, default=1)
    parser.add_argument("--resume-days", type=int, default=RESUME_DAYS)
    parser.add_argument("--force", action="store_true", help="Bỏ qua resume")
    parser.add_argument("--sleep", type=float, default=3.0, help="Nghỉ giữa các mã (chỉ khi dùng AI)")

    # 🎯 FLAG MỚI: Chọn dùng AI hay không
    parser.add_argument("--no-ai", action="store_true",
                        help="KHÔNG gọi AI, chỉ dùng template fallback (miễn phí, không cần API key)")
    parser.add_argument("--ai", dest="use_ai", action="store_true", default=None,
                        help="BẮT BUỘC dùng AI (mặc định: tự động nếu có API key)")
    parser.add_argument("--auto", dest="use_ai", action="store_false",
                        help="Tự động: dùng AI nếu có API key, không thì template")

    args = parser.parse_args()

    # Xác định use_ai
    if args.no_ai:
        use_ai = False
    elif args.use_ai is True:
        use_ai = True
        if not ALIBABA_API_KEY:
            print("❌ Bạn chỉ định --ai nhưng thiếu ALIBABA_API_KEY. Không thể chạy AI.")
            return
    elif args.use_ai is False:
        use_ai = False
    else:
        # Mặc định: dùng AI nếu có key
        use_ai = bool(ALIBABA_API_KEY)

    source = "AI" if use_ai else "TEMPLATE"
    if use_ai:
        print(f"🤖 Chế độ: AI (model qwen3.7-max)")
    else:
        if not ALIBABA_API_KEY:
            print(f"📝 Chế độ: TEMPLATE fallback (không có ALIBABA_API_KEY)")
        else:
            print(f"📝 Chế độ: TEMPLATE fallback (do --no-ai / --auto)")

    if not os.path.exists(SCREENER_FILE) or not os.path.exists(DATA_FILE):
        print(f"❌ Không tìm thấy file dữ liệu đầu vào!")
        return

    with open(SCREENER_FILE, "r", encoding="utf-8") as f:
        screener_data = json.load(f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    screener_map = {item.get('symbol'): item for item in screener_data if item.get('close_price', 0) > 0}

    if INPUT_SYMBOLS:
        custom_list = [s.strip().upper() for s in INPUT_SYMBOLS.split(",") if s.strip()]
        print(f"🎯 INPUT_SYMBOLS: {custom_list}")
        custom_map = {s: get_sector(s) for s in custom_list if s in screener_map}
        count = run_group(custom_map, "INPUT_SYMBOLS", stock_db, screener_map, args.sleep, use_ai=use_ai)
        print(f"\n🎉 Hoàn thành: {count} mã.")
        return

    print("=" * 60)
    print(f"PHÂN LOẠI MÃ | NGUỒN: {source}")
    print("=" * 60)
    top_symbols, remaining_symbols = build_target_lists(screener_map)

    print(f"\n🔝 Top đầu: {len(top_symbols)} mã")
    print(f"📦 Còn lại: {len(remaining_symbols)} mã")

    if not args.force and args.resume_days > 0:
        top_before = len(top_symbols)
        top_symbols = {s: sec for s, sec in top_symbols.items()
                       if not is_recently_analyzed(stock_db.get(s, {}), args.resume_days)}
        rem_before = len(remaining_symbols)
        remaining_symbols = {s: sec for s, sec in remaining_symbols.items()
                              if not is_recently_analyzed(stock_db.get(s, {}), args.resume_days)}
        print(f"\n⏭️  Resume ({args.resume_days} ngày):")
        print(f"   - Top: bỏ qua {top_before - len(top_symbols)} mã")
        print(f"   - Còn lại: bỏ qua {rem_before - len(remaining_symbols)} mã")

    total_count = 0

    if args.mode in ("top", "all"):
        if top_symbols:
            total_count += run_group(top_symbols, "TOP", stock_db, screener_map, args.sleep, use_ai=use_ai)
        else:
            print("✅ Top đầu: đã phân tích gần đây, bỏ qua.")

    if args.mode in ("rest", "all"):
        if remaining_symbols:
            remaining_sorted = sorted(remaining_symbols.keys())
            total_rem = len(remaining_sorted)
            total_batches = args.total_batches if args.total_batches >= 1 else 1
            per_batch = (total_rem + total_batches - 1) // total_batches
            start_idx = (args.batch - 1) * per_batch
            end_idx = min(start_idx + per_batch, total_rem)
            batch_symbols = remaining_sorted[start_idx:end_idx]

            if not batch_symbols:
                print(f"⚠️ Batch {args.batch}/{total_batches} rỗng.")
            else:
                batch_map = {s: remaining_symbols[s] for s in batch_symbols}
                print(f"\n📦 Batch {args.batch}/{total_batches}: {len(batch_map)}/{total_rem} mã")
                total_count += run_group(batch_map, f"REST-{args.batch}/{total_batches}",
                                         stock_db, screener_map, args.sleep, use_ai=use_ai)
        else:
            print("✅ Phần còn lại: đã phân tích gần đây, bỏ qua.")

    print(f"\n🎉 Hoàn thành: cập nhật {total_count} mã vào {DATA_FILE}.")
    print(f"📌 Nguồn: {source}")


if __name__ == "__main__":
    main()
