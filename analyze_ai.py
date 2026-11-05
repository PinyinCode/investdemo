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


# ============================================================
# 🎯 HƯỚNG DẪN THEO NGÀNH — CHỈ DẪN CÁCH ĐỌC SỐ LIỆU, KHÔNG BỊA
# ============================================================
def get_sector_guidance(sector):
    guidance = {
        "NGAN_HANG": (
            "ĐẶC THÙ NGÂN HÀNG: D/E cao (5-15x) là bản chất vì nợ = tiền gửi KH. "
            "CFO âm khi mở rộng tín dụng là bình thường (cho vay nhiều hơn huy động). "
            "Trọng tâm: ROE, ROA, tăng trưởng tín dụng (credit_growth_yoy), NIM."
        ),
        "CHUNG_KHOAN": (
            "ĐẶC THÙ CHỨNG KHOÁN: Doanh thu phụ thuộc thanh khoản TT chung + margin + tự doanh. "
            "Trọng tâm: ROE, tăng trưởng LNST YoY, chu kỳ thanh khoản thị trường."
        ),
        "BAT_DONG_SAN": (
            "ĐẶC THÙ BẤT ĐỘNG SẢN: Doanh thu ghi nhận theo tiến độ dự án (không đều giữa các quý). "
            "Trọng tâm: P/B (định giá quỹ đất), ROE, dòng tiền người mua trả trước."
        ),
        "CONG_NGHE_BAN_LE": (
            "ĐẶC THÙ CÔNG NGHỆ/BÁN LẺ: Tăng trưởng doanh thu là ưu tiên số 1. "
            "Trọng tâm: ROE, biên lợi nhuận gộp, tăng trưởng LNST YoY."
        ),
        "DIEN_NUOC_HA_TANG": (
            "ĐẶC THÙ TIỆN ÍCH: Khấu hao lớn che lấp lợi nhuận kế toán nhưng CFO ổn định. "
            "Trọng tâm: ROE, cổ tức tiền mặt, sự ổn định của CFO."
        ),
        "NGUYEN_VAT_LIEU_CHU_KY": (
            "ĐẶC THÙ VẬT LIỆU CHU KỲ: Biên gộp biến động mạnh theo giá hàng hóa. "
            "Cẩn thận bẫy P/E thấp tại đỉnh chu kỳ (lợi nhuận đỉnh → P/E trông rẻ giả tạo). "
            "Trọng tâm: P/B, ROE, biên gộp."
        ),
        "SAN_XUAT_TIEU_DUNG_PHONG_THU": (
            "ĐẶC THÙ SẢN XUẤT/TIÊU DÙNG: Đánh giá sức mạnh thương hiệu, thị phần. "
            "Trọng tâm: ROE, biên gộp, CFO/LNST (phải ≥ 0.8x để xác nhận lợi nhuận thật)."
        ),
    }
    return guidance.get(sector, guidance["SAN_XUAT_TIEU_DUNG_PHONG_THU"])


# ============================================================
# 🧮 XÂY DỰNG DỮ KIỆN ĐÃ KIỂM CHỨNG CHO PROMPT
# AI CHỈ ĐƯỢC ĐỌC, KHÔNG ĐƯỢC BỊA
# ============================================================
def build_verified_facts(symbol, stock_metrics, screener_item, sector):
    """Tổng hợp mọi số liệu đã có trong data.json + screener_results.json thành 1 khối text."""
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

    # Các trường được screener.py tính sẵn
    fair_low = float(stock_metrics.get("fair_value_low", 0) or 0)
    fair_high = float(stock_metrics.get("fair_value_high", 0) or 0)
    graham = float(stock_metrics.get("graham_number", 0) or 0)
    mos_pct = float(stock_metrics.get("margin_of_safety_pct", 0) or 0)
    discount_pct = float(stock_metrics.get("discount_to_fair_pct", 0) or 0)
    verdict = stock_metrics.get("valuation_verdict", "CHƯA TÍNH")
    rationale = stock_metrics.get("fair_value_rationale", "")
    methods = stock_metrics.get("fair_value_methods", {})
    sub_sector = stock_metrics.get("sub_sector", sector)

    # Từ screener_results.json
    growth_yoy = float(screener_item.get("profit_growth_yoy", 0) or 0)
    total_score = screener_item.get("total_score", 0)
    fund_score = screener_item.get("fundamental_score", 0)
    val_score = screener_item.get("valuation_score", 0)
    tech_score = screener_item.get("technical_score", 0)
    fund_notes = screener_item.get("fundamental_notes", "")
    potential_zone = screener_item.get("potential_zone", "")
    technical_status = screener_item.get("technical_status", "")
    pattern = screener_item.get("pattern", "")

    # CFO/LNST (chất lượng lợi nhuận)
    cfo_quality = ""
    if npat > 0 and cfo != 0:
        ratio = cfo / npat
        cfo_quality = f" | CFO/LNST = {ratio:.2f}x"
        if ratio >= 1.0:
            cfo_quality += " (lợi nhuận thật, có tiền mặt)"
        elif ratio >= 0.8:
            cfo_quality += " (chất lượng tốt)"
        elif ratio >= 0.5:
            cfo_quality += " (chấp nhận được)"
        elif ratio > 0:
            cfo_quality += " (cần lưu ý - lợi nhuận kém tiền mặt)"
        else:
            cfo_quality += " (⚠️ CẢNH BÁO - CFO âm)"

    # P/E, P/B so với vùng mua
    fair_position = ""
    if fair_low > 0 and close > 0:
        if close <= fair_low:
            fair_position = f"✅ Giá hiện tại ĐANG TRONG VÙNG MUA (thấp hơn fair_low {discount_pct:.1f}%)"
        elif close <= fair_high:
            fair_position = f"⚖️ Giá hợp lý, cần chờ điều chỉnh về fair_low {fair_low:,.0f}"
        elif close <= fair_high * 1.2:
            fair_position = f"⚠️ Giá HƠI ĐẮT (cao hơn fair_high {((close-fair_high)/fair_high*100):.1f}%)"
        else:
            fair_position = f"❌ Giá ĐẮT (cao hơn fair_high {((close-fair_high)/fair_high*100):.1f}%)"

    lines = [
        f"=== MÃ {symbol} — NGÀNH {sector} — SUB-SECTOR {sub_sector} ===",
        "",
        "[1] GIÁ & ĐỊNH GIÁ HIỆN TẠI",
        f"  - Giá thị trường: {close:,.0f} VNĐ",
        f"  - P/E = {pe:.2f}x | P/B = {pb:.2f}x | P/S = {ps:.2f}x",
        f"  - EPS = {eps:,.0f} VNĐ | BVPS = {bvps:,.0f} VNĐ",
        f"  - Cổ tức: {div_yield}%/năm",
        "",
        "[2] VÙNG MUA ĐÃ TÍNH BỞI HỆ THỐNG (DETERMINISTIC)",
        f"  - Fair value (giá trị hợp lý): {fair_high:,.0f} VNĐ",
        f"  - Vùng mua an toàn (fair_low): {fair_low:,.0f} VNĐ",
        f"  - Biên an toàn áp dụng: {mos_pct:.1f}%",
        f"  - Graham Number: {graham:,.0f} VNĐ" if graham > 0 else "  - Graham Number: N/A (ngành tài chính)",
        f"  - Chi tiết phương pháp: {json.dumps(methods, ensure_ascii=False)}",
        f"  - Cơ sở tính: {rationale}",
        f"  - Vị thế giá hiện tại: {fair_position}",
        f"  - Verdict hệ thống: {verdict}",
        "",
        "[3] HIỆU QUẢ SINH LỜI & CHẤT LƯỢNG",
        f"  - ROE = {roe}% | ROA = {roa}%",
        f"  - Lợi nhuận TTM = {npat:,.0f} Tỷ | CFO = {cfo:,.0f} Tỷ{cfo_quality}",
        f"  - D/E = {de:.2f} | Biên gộp = {gm}%",
        f"  - Tăng trưởng LNST YoY = {growth_yoy}%",
        "",
        "[4] ĐIỂM SỐ HỆ THỐNG (screener.py)",
        f"  - Tổng điểm: {total_score}/100 (Cơ bản {fund_score}/50, Định giá {val_score}/30, Kỹ thuật {tech_score}/20)",
        f"  - Ghi chú cơ bản: {fund_notes}",
        f"  - Vùng tiềm năng: {potential_zone}",
        f"  - Trạng thái kỹ thuật: {technical_status} | Mẫu hình: {pattern}",
    ]
    return "\n".join(lines)


# ============================================================
# 🤖 GỌI AI — CHỈ ĐỂ DIỄN GIẢI
# ============================================================
def analyze_stock_with_ai(symbol, stock_metrics, screener_item, sector):
    if not ALIBABA_API_KEY:
        print(f"❌ LỖI: Biến môi trường ALIBABA_API_KEY đang trống!")
        return None

    # Chuẩn bị dữ kiện
    verified_facts = build_verified_facts(symbol, stock_metrics, screener_item, sector)
    sector_guidance = get_sector_guidance(sector)

    fair_low = float(stock_metrics.get("fair_value_low", 0) or 0)
    fair_high = float(stock_metrics.get("fair_value_high", 0) or 0)
    verdict = stock_metrics.get("valuation_verdict", "CHƯA TÍNH")
    discount_pct = float(stock_metrics.get("discount_to_fair_pct", 0) or 0)
    close_price = float(stock_metrics.get("close", stock_metrics.get("close_price", 0)) or 0)

    prompt = f"""Bạn là Chuyên gia Phân tích Đầu tư Giá trị (Value Investing) với 20 năm kinh nghiệm tại các quỹ lớn ở Việt Nam (VinaCapital, Dragon Capital, SSI Asset Management).

NHIỆM VỤ: Diễn giải dữ liệu đã được tính toán sẵn cho mã {symbol}. Bạn KHÔNG được bịa số liệu. Mọi con số phải TRÍCH DẪN TRỰC TIẾP từ khối DỮ KIỆN bên dưới.

--- DỮ KIỆN ĐÃ KIỂM CHỨNG (BẮT BUỘC DÙNG ĐÚNG SỐ NÀY) ---
{verified_facts}

--- HƯỚNG DẪN ĐỌC SỐ LIỆU THEO NGÀNH ---
{sector_guidance}

--- QUY TẮC BẮT BUỘC (VI PHẠM = BÀI VIẾT SAI) ---
1. MỌI nhận định phải có SỐ CỤ THỂ trích từ dữ kiện trên. Ví dụ ĐÚNG: "P/E 7.39 thấp hơn median ngành ngân hàng ~9x". Ví dụ SAI: "P/E rất hấp dẫn" (không có số).
2. VỀ VÙNG MUA: Bạn PHẢI dùng đúng 2 con số đã tính:
   - Fair value: {fair_high:,.0f} VNĐ
   - Vùng mua an toàn: {fair_low:,.0f} VNĐ
   TUYỆT ĐỐI KHÔNG được tự nghĩ ra con số khác (như 20k, 18k, 25k...). Nếu muốn nói "vùng gom giá trị", PHẢI dùng {fair_low:,.0f}.
3. VỀ KHUYẾN NGHỊ:
   - Nếu Verdict = "RẺ - TRONG VÙNG MUA" → recommendation PHẢI là "MUA TÍCH SẢN" hoặc "MUA MẠNH".
   - Nếu Verdict = "HỢP LÝ - CHỜ ĐIỀU CHỈNH" → recommendation PHẢI là "NẮM GIỮ" hoặc "CHỜ VỀ VÙNG MUA".
   - Nếu Verdict = "HƠI ĐẮT - KHÔNG MUA" → recommendation PHẢI là "CHỜ VỀ VÙNG MUA".
   - Nếu Verdict = "ĐẮT - TRÁNH" → recommendation PHẢI là "TRÁNH".
   - Nếu Verdict = "KHÔNG ĐỦ DỮ LIỆU" → recommendation PHẢI là "CHƯA ĐỦ CƠ SỞ - THEO DÕI".
4. KHÔNG dùng từ hoa mỹ chung chung ("cực kỳ hấp dẫn", "vàng son", "thiên thời"...). Viết như báo cáo đầu tư nội bộ.
5. Nếu phát hiện mâu thuẫn giữa verdict và số liệu, hãy chỉ ra mâu thuẫn đó thay vì che giấu.

--- ĐỊNH DẠNG TRẢ VỀ: JSON THUẦN TÚY (KHÔNG BỌC ```json) ---
{{
  "bctc": "6-8 câu phân tích sức khỏe tài chính. BẮT BUỘC trích các số: ROE={stock_metrics.get('roe',0)}%, ROA={stock_metrics.get('roa',0)}%, P/E={stock_metrics.get('pe',0)}, P/B={stock_metrics.get('pb',0)}, CFO/LNST, D/E={stock_metrics.get('debt_to_equity',0)}, biên gộp nếu áp dụng. Kết luận rõ: lợi nhuận thật hay ảo? Chất lượng tài sản tốt hay xấu?",
  "catalyst": "3-4 câu. Nêu Economic Moat CỤ THỂ (thương hiệu/thị phần/chi phí chuyển đổi/quy mô) + 1 động lực tăng trưởng 2-3 năm tới. Không chung chung.",
  "risks": "3 câu. Rủi ro TRỌNG YẾU NHẤT phù hợp ngành (nợ xấu, pha loãng, giá nguyên liệu, chính sách...). Không liệt kê lan man.",
  "valuation_verdict": "Copy nguyên văn từ dữ kiện: '{verdict}'",
  "outlook": "4-5 câu. So sánh giá {close_price:,.0f} với vùng mua an toàn {fair_low:,.0f}-{fair_high:,.0f}. Giải thích vì sao {verdict} dựa trên {discount_pct:.1f}% chiết khấu. Đánh giá biên an toàn thực tế.",
  "recommendation": "1 trong 5 giá trị: 'MUA MẠNH' | 'MUA TÍCH SẢN' | 'NẮM GIỮ' | 'CHỜ VỀ VÙNG MUA' | 'TRÁNH'. Kèm tỷ trọng % (VD: 'MUA TÍCH SẢN — Tỷ trọng 10-15%').",
  "price_zone": "BẮT BUỘC format: 'Vùng mua: {fair_low:,.0f} — {fair_high:,.0f} | Giá hiện tại: {close_price:,.0f} | Verdict: {verdict}'. KHÔNG ĐƯỢC BỊA SỐ KHÁC.",
  "macro_view": "4-5 câu. Chỉ nêu yếu tố vĩ mô/chu kỳ THỰC SỰ ảnh hưởng doanh nghiệp này (lãi suất, chính sách ngành, chu kỳ hàng hóa). Không nói chung về VN-Index."
}}"""

    headers = {"Authorization": f"Bearer {ALIBABA_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "qwen3.7-max",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15,  # Thấp để bám dữ liệu
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

                # Chuẩn hóa price_zone nếu AI trả dict
                raw_pz = parsed_data.get("price_zone", "")
                if isinstance(raw_pz, dict):
                    parsed_data["price_zone"] = " | ".join([f"{k}: {v}" for k, v in raw_pz.items()])
                elif isinstance(raw_pz, list):
                    parsed_data["price_zone"] = " - ".join([str(i) for i in raw_pz])
                else:
                    parsed_data["price_zone"] = str(raw_pz)

                # Kiểm tra AI có bịa số trong price_zone không
                if fair_low > 0:
                    pz_text = parsed_data["price_zone"]
                    # Nếu AI bịa số lạ không có trong fair_low/fair_high/close → cảnh báo
                    numbers_in_pz = re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d{4,}", pz_text)
                    allowed = {f"{int(fair_low):,}", f"{int(fair_high):,}", f"{int(close_price):,}"}
                    for num in numbers_in_pz:
                        if num not in allowed and num.replace(",", "").replace(".", "") not in [str(int(fair_low)), str(int(fair_high)), str(int(close_price))]:
                            print(f"  ⚠️ [{symbol}] AI có thể bịa số trong price_zone: {num}")
                            # Ghi đè nếu AI bịa
                            parsed_data["price_zone"] = (
                                f"Vùng mua: {fair_low:,.0f} — {fair_high:,.0f} | "
                                f"Giá hiện tại: {close_price:,.0f} | Verdict: {verdict}"
                            )
                            break

                return parsed_data
            else:
                print(f"[{symbol}] Lỗi HTTP {response.status_code}: {response.text[:200]}")
                break
        except requests.exceptions.Timeout:
            print(f"[{symbol}] ⏳ Timeout lần {attempt + 1}/3, thử lại...")
            time.sleep(3)
        except Exception as e:
            print(f"[{symbol}] Lỗi AI: {e}")
            break

    return None


# ============================================================
# BUILD TARGET LISTS & RUN (giữ nguyên)
# ============================================================
def build_target_lists(screener_map):
    industry_groups = {}
    for symbol, item in screener_map.items():
        sector = get_sector(symbol)
        item['sector'] = sector
        industry_groups.setdefault(sector, []).append(item)

    top_symbols = {}
    for sector, items in industry_groups.items():
        items_sorted = sorted(
            items,
            key=lambda x: (x.get('fundamental_score', 0), x.get('dividend_yield', 0), x.get('roe', 0)),
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


def run_group(symbols_dict, label, stock_db, screener_map, sleep_time):
    if not symbols_dict:
        print(f"⚠️ Nhóm [{label}] rỗng, bỏ qua.")
        return 0

    symbols_sorted = sorted(symbols_dict.keys())
    total = len(symbols_sorted)
    count = 0

    print(f"\n🚀 Nhóm [{label}]: {total} mã")
    print(f"   Danh sách: {symbols_sorted}\n")

    for idx, symbol in enumerate(symbols_sorted, 1):
        sector = symbols_dict[symbol]
        if symbol not in stock_db:
            stock_db[symbol] = {}
        if symbol not in screener_map:
            continue

        stock_metrics = stock_db[symbol]
        screener_item = screener_map[symbol]

        # Kiểm tra xem đã có vùng mua chưa
        if float(stock_metrics.get("fair_value_low", 0) or 0) == 0:
            print(f"[{idx}/{total}] ⚠️ [{sector}] {symbol} — CHƯA CÓ VÙNG MUA (chạy screener.py trước). Bỏ qua.")
            continue

        print(f"[{idx}/{total}] 🔍 [{sector}] {symbol} | Fair: {stock_metrics.get('fair_value_low',0):,.0f}-{stock_metrics.get('fair_value_high',0):,.0f} | Verdict: {stock_metrics.get('valuation_verdict','?')}")
        ai_result = analyze_stock_with_ai(symbol, stock_metrics, screener_item, sector)

        if ai_result:
            stock_metrics["bctc"] = ai_result.get("bctc", "")
            stock_metrics["catalyst"] = ai_result.get("catalyst", "")
            stock_metrics["risks"] = ai_result.get("risks", "")
            stock_metrics["outlook"] = ai_result.get("outlook", "")
            stock_metrics["ai_recommendation"] = ai_result.get("recommendation", "")
            stock_metrics["ai_price_zone"] = ai_result.get("price_zone", "")
            stock_metrics["macro_view"] = ai_result.get("macro_view", "")
            stock_metrics["ai_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            count += 1
            print(f"  -> ✅ OK ({count}/{total})")
        else:
            print(f"  -> ❌ Lỗi AI")

        save_db(stock_db)
        time.sleep(sleep_time)

    return count


def main():
    parser = argparse.ArgumentParser(description="AI analysis dựa trên dữ liệu đã kiểm chứng")
    parser.add_argument("--mode", choices=["top", "rest", "all"], default="top")
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--total-batches", type=int, default=1)
    parser.add_argument("--resume-days", type=int, default=RESUME_DAYS)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sleep", type=float, default=3.0)
    args = parser.parse_args()

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
        count = run_group(custom_map, "INPUT_SYMBOLS", stock_db, screener_map, args.sleep)
        print(f"\n🎉 Hoàn thành: {count} mã.")
        return

    print("=" * 60)
    print("PHÂN LOẠI MÃ: TOP ĐẦU MỖI NGÀNH vs PHẦN CÒN LẠI")
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
            total_count += run_group(top_symbols, "TOP", stock_db, screener_map, args.sleep)
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
                print(f"\n📦 Batch {args.batch}/{total_batches} của phần CÒN LẠI: {len(batch_map)}/{total_rem} mã")
                total_count += run_group(batch_map, f"REST-{args.batch}/{total_batches}",
                                         stock_db, screener_map, args.sleep)
        else:
            print("✅ Phần còn lại: đã phân tích gần đây, bỏ qua.")

    print(f"\n🎉 Hoàn thành: cập nhật {total_count} mã vào {DATA_FILE}.")


if __name__ == "__main__":
    main()
