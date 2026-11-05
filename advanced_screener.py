from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
from ptkt import (
    ProfessionalTechnicalAnalyzer,
)  # Gọi module PTKT chuyên nghiệp từ ptkt.py

DATA_FILE = "data.json"
BCTC_DIR = "bctc_data"
OUTPUT_JSON = "screener_results.json"
OUTPUT_CSV = "screener_summary.csv"

# Phân nhóm ngành chuẩn chi tiết cho VN100 (7 Nhóm ngành)
SECTOR_MAPPING = {
    "NGAN_HANG": [
        "ACB",
        "BID",
        "CTG",
        "TCB",
        "MBB",
        "STB",
        "VPB",
        "HDB",
        "VIB",
        "TPB",
        "SHB",
        "SSB",
        "LPB",
        "MSB",
        "OCB",
        "EIB",
        "VCB",
    ],
    "CHUNG_KHOAN": ["SSI", "VCI", "HCM", "VIX", "MBS", "FTS", "BSI", "CTS", "ORS"],
    "BAT_DONG_SAN": [
        "VHM",
        "VIC",
        "VRE",
        "NVL",
        "PDR",
        "DIG",
        "NLG",
        "KDH",
        "CEO",
        "DXG",
        "TCH",
        "HDG",
        "KBC",
        "IDC",
        "SZC",
        "BCM",
        "PHR",
        "SJS",
        "VPI",
    ],
    "CONG_NGHE_BAN_LE": ["FPT", "MWG", "PNJ", "FRT", "DGW"],
    "DIEN_NUOC_HA_TANG": ["POW", "REE", "PC1", "NT2", "GAS", "GEG", "BWE", "TDM"],
    "NGUYEN_VAT_LIEU_CHU_KY": [
        "HPG",
        "HSG",
        "NKG",
        "DGC",
        "DCM",
        "DPM",
        "GVR",
        "PHR",
        "DHC",
    ],
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": [
        "VNM",
        "MSN",
        "SAB",
        "VHC",
        "ANV",
        "BVH",
        "PLX",
        "PVD",
        "PVS",
        "BSR",
        "GMD",
        "HAH",
        "PVT",
        "HVN",
        "APH",
        "ASM",
        "DBC",
        "KDC",
        "MSH",
        "PAN",
        "SBT",
        "DRC",
        "CSM",
        "BMP",
        "DHG",
        "CTD",
        "VCG",
        "HHV",
        "GEX",
    ],
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


def evaluate_stock(symbol, data):
    sector = get_sector(symbol)
    
    # Lấy các chỉ số, hỗ trợ fallback an toàn nếu bằng 0 hoặc None
    pe = data.get("pe", 0) or 0
    pb = data.get("pb", 0) or 0
    ps = data.get("ps", 0) or 0
    roe = data.get("roe", 0) or 0
    roa = data.get("roa", 0) or 0
    dividend_yield = data.get("dividend_yield", 0) or 0
    close_price = data.get("close", 0) or 0

    cfo_latest = data.get("cfo_latest", 0) or 0
    net_profit_ttm = data.get("net_profit_ttm", 0) or 0
    debt_to_equity = data.get("debt_to_equity", 0) or 0
    gross_margin = data.get("gross_margin", 0) or 0

    # Nếu thiếu thông số định giá trực tiếp, thử tra cứu fallback từ ratios trong bctc_data
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

    # =========================================================================
    # 1. ĐIỂM CƠ BẢN (50 điểm) - CHẤT LƯỢNG DOANH NGHIỆP (Tách hoàn toàn P/E, P/B)
    # =========================================================================
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

    else:  # SAN_XUAT_TIEU_DUNG_PHONG_THU
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
        if cfo_latest > 0 and (
            net_profit_ttm <= 0 or cfo_latest >= net_profit_ttm * 0.8
        ):
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
            fund_notes.append(
                f"⚠️ Cảnh báo: Đòn bẩy nợ cao (D/E: {debt_to_equity})"
            )
    else:
        if dividend_yield >= 4.0:
            fundamental_score += 5
            fund_notes.append(f"Cổ tức tiền mặt tốt ({dividend_yield}%)")
        else:
            fundamental_score += 5
            fund_notes.append("Ngân hàng tối ưu giữ vốn mở rộng")

    fundamental_score = int(np.clip(fundamental_score, 0, 50))

    # =========================================================================
    # 2. ĐIỂM ĐỊNH GIÁ (30 điểm) - ĐỊNH GIÁ LINH HOẠT THEO NGÀNH (Giải quyết điểm mù)
    # =========================================================================
    valuation_score = 0

    if sector == "BAT_DONG_SAN":
        # BĐS: Định giá theo P/B (tài sản sổ sách/quỹ đất) và P/S (doanh thu/dòng tiền đặt cọc)
        if (0 < pb < 1.5) or (0 < ps < 2.0):
            valuation_score = 30
        elif (0 < pb < 2.2) or (0 < ps < 3.5):
            valuation_score = 18
        else:
            valuation_score = 8

    elif sector == "NGUYEN_VAT_LIEU_CHU_KY":
        # Ngành chu kỳ: Tránh bẫy P/E đắt ở đáy chu kỳ bằng cách dùng P/S kết hợp P/E
        if (0 < ps < 1.2) or (0 < pe < 12):
            valuation_score = 30
        elif (0 < ps < 2.0) or (0 < pe < 18):
            valuation_score = 18
        else:
            valuation_score = 8

    elif sector == "CONG_NGHE_BAN_LE":
        # Ngành tăng trưởng: Cho phép P/E cao hơn nếu tăng trưởng tốt
        if 0 < pe < 18 or (profit_growth_yoy > 20 and pe < 25):
            valuation_score = 30
        elif 0 < pe < 25:
            valuation_score = 18
        else:
            valuation_score = 8

    elif sector in ["NGAN_HANG", "CHUNG_KHOAN"]:
        # Ngân hàng & Chứng khoán: Định giá P/B tương quan với khả năng sinh lời ROE
        if 0 < pb < 1.3 or (roe >= 16 and pb < 1.8):
            valuation_score = 30
        elif 0 < pb < 2.0:
            valuation_score = 18
        else:
            valuation_score = 8

    else:
        # Tiêu dùng, Hạ tầng: Chuẩn P/E kết hợp Cổ tức
        if 0 < pe < 15 or dividend_yield >= 5.0:
            valuation_score = 30
        elif 0 < pe < 20 or dividend_yield >= 3.0:
            valuation_score = 18
        else:
            valuation_score = 8

    valuation_score = int(np.clip(valuation_score, 0, 30))

    # =========================================================================
    # 3. ĐIỂM KỸ THUẬT (20 điểm) - Đọc từ history/*.json qua ptkt.py
    # =========================================================================
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
            technical_status = ptkt_res.get(
                "technical_status", "Tích lũy sideway"
            )
            pattern = ptkt_res.get("pattern", "Tích lũy")
            volume_analysis = ptkt_res.get("volume_analysis", "")
        except Exception as e:
            print(f"⚠️ Lỗi phân tích kỹ thuật {symbol}: {e}")

    # Quy đổi điểm kỹ thuật từ thang 100 về thang chuẩn 20 điểm
    technical_score = int(round((technical_score_raw / 100.0) * 20))
    technical_score = int(np.clip(technical_score, 0, 20))

    # TỔNG ĐIỂM QUY CHUẨN (50 PTCB + 30 Định giá + 20 PTKT = 100 điểm)
    total_score = fundamental_score + valuation_score + technical_score

    potential_zone = "THEO DÕI THÊM"
    if total_score >= 75:
        potential_zone = "VÙNG TÍCH SẢN TỐI ƯU (A+)"
    elif total_score >= 60:
        potential_zone = "VÙNG MUA AN TOÀN (B)"

    return {
        "symbol": symbol,
        "sector": sector,
        "close_price": close_price,
        "pe": pe,
        "pb": pb,
        "ps": ps,
        "roe": roe,
        "roa": roa,
        "dividend_yield": dividend_yield,
        "profit_growth_yoy": profit_growth_yoy,
        "cfo_latest": cfo_latest,
        "debt_to_equity": debt_to_equity,
        "gross_margin": gross_margin,
        "fundamental_score": fundamental_score,  # Tối đa 50đ
        "valuation_score": valuation_score,      # Tối đa 30đ
        "technical_score": technical_score,      # Tối đa 20đ
        "total_score": total_score,              # Tối đa 100đ
        "potential_zone": potential_zone,
        "pattern": pattern,
        "technical_status": technical_status,
        "volume_analysis": volume_analysis,
        "fundamental_notes": " | ".join(fund_notes),
    }


def main():
    print(
        "🚀 Chạy bộ lọc định lượng Quant: PTCB (50đ) + Định giá Ngành (30đ) + PTKT & Volume (20đ)..."
    )

    if not os.path.exists(DATA_FILE):
        print(f"⚠️ Không tìm thấy file {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    results = []
    for symbol, data in stock_db.items():
        res = evaluate_stock(symbol, data)
        if res:
            results.append(res)

    if not results:
        print("⚠️ Không có dữ liệu để xử lý.")
        return

    # Sắp xếp theo tổng điểm từ cao xuống thấp, ưu tiên điểm cơ bản
    results = sorted(
        results,
        key=lambda x: (
            x.get("total_score", 0),
            x.get("fundamental_score", 0),
        ),
        reverse=True,
    )

    # Ghi ra file JSON cho Web (index.html)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)

    # Ghi ra file CSV cho Excel
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n✅ Hoàn tất thành công!")
    print(f"   - Đã cập nhật file kết quả JSON: {OUTPUT_JSON}")
    print(f"   - Đã xuất file tổng hợp Excel: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
