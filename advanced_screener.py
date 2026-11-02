import os
import json
import pandas as pd
import numpy as np

DATA_FILE = "data.json"
OUTPUT_JSON = "screener_results.json"
OUTPUT_CSV = "screener_summary.csv"

# Phân nhóm ngành chuẩn cho đủ 100 mã VN100
SECTOR_MAPPING = {
    "NGAN_HANG": [
        "ACB", "BID", "CTG", "TCB", "MBB", "STB", "VPB", "HDB", "VIB", "TPB",
        "SHB", "SSB", "LPB", "MSB", "OCB", "EIB", "VCB"
    ],
    "CHUNG_KHOAN": [
        "SSI", "VCI", "HCM", "VIX", "MBS", "FTS", "BSI", "CTS", "ORS"
    ],
    "BAT_DONG_SAN": [
        "VHM", "VIC", "VRE", "NVL", "PDR", "DIG", "NLG", "KDH", "CEO", "DXG",
        "TCH", "HDG", "KBC", "IDC", "SZC", "BCM", "PHR", "SJS", "VPI"
    ],
    "SAN_XUAT_TIEU_DUNG": [
        "HPG", "HSG", "NKG", "CTD", "VCG", "HHV", "FPT", "MWG", "PNJ", "FRT",
        "VNM", "MSN", "SAB", "GAS", "PVD", "PVS", "BSR", "POW", "REE", "PC1",
        "NT2", "GMD", "HAH", "PVT", "VJC", "HVN", "VHC", "ANV", "BVH", "GVR",
        "PLX", "APH", "ASM", "DBC", "DCM", "DPM", "GEX", "KDC", "LIG", "MSH",
        "PAN", "SBT", "TCD", "TLG", "VDP", "VPG", "VTO", "DHC", "IMP", "SBA",
        "TID", "DRC", "CSM", "BMP", "NTC", "DHG", "VOS", "HAG"
    ]
}

def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG"

def evaluate_stock(symbol, data):
    sector = get_sector(symbol)
    pe = data.get("pe", 0)
    pb = data.get("pb", 0)
    roe = data.get("roe", 0)
    dividend_yield = data.get("dividend_yield", 0)
    recommendation = data.get("recommendation", "")
    close_price = data.get("close", 0)
    
    bctc_history = data.get("bctc_history", [])
    if not bctc_history:
        return None
        
    latest = bctc_history[0]
    net_profit = latest.get("net_profit", 0)
    profit_growth_yoy = latest.get("profit_growth_yoy", 0)
    credit_growth_yoy = latest.get("credit_growth_yoy", 0)

    # =========================================================================
    # 1. CHẤM ĐIỂM CƠ BẢN (50 điểm) - THIẾT KẾ RIÊNG BIỆT THEO TỪNG NHÓM NGÀNH
    # =========================================================================
    fundamental_score = 0
    fund_notes = []

    if sector == "NGAN_HANG":
        # Ngân hàng: Ưu tiên Tín dụng mạnh (25đ) và ROE cao (25đ). Ít xét cổ tức do cần giữ vốn.
        if credit_growth_yoy >= 12: 
            fundamental_score += 25; fund_notes.append("Tín dụng mạnh (>=12%)")
        elif credit_growth_yoy >= 8:
            fundamental_score += 15; fund_notes.append("Tín dụng khá")
            
        if roe >= 18: 
            fundamental_score += 25; fund_notes.append("ROE xuất sắc (>=18%)")
        elif roe >= 14: 
            fundamental_score += 15; fund_notes.append("ROE tốt (>=14%)")

    elif sector == "CHUNG_KHOAN":
        # Chứng khoán: Ưu tiên tốc độ tăng trưởng lợi nhuận đột phá (30đ) và Biên sinh lời ROE (20đ)
        if profit_growth_yoy >= 20: 
            fundamental_score += 30; fund_notes.append("LN tăng trưởng mạnh (>=20%)")
        elif profit_growth_yoy >= 10:
            fundamental_score += 15; fund_notes.append("LN hồi phục tốt")
            
        if roe >= 15: 
            fundamental_score += 20; fund_notes.append("ROE chứng khoán cao (>=15%)")
        elif roe >= 10:
            fundamental_score += 10; fund_notes.append("ROE ổn định")

    elif sector == "BAT_DONG_SAN":
        # Bất động sản: Ưu tiên biên an toàn vốn, khả năng giữ vững quy mô lợi nhuận và ROE cơ bản
        if profit_growth_yoy >= 10: 
            fundamental_score += 25; fund_notes.append("LN giữ nhịp tăng trưởng")
        if roe >= 12: 
            fundamental_score += 25; fund_notes.append("ROE BĐS đạt chuẩn (>=12%)")
        elif roe > 0:
            fundamental_score += 10; fund_notes.append("Có lãi dương")

    else: 
        # NHÓM SẢN XUẤT & TIÊU DÙNG: TRỌNG TÂM LÀ CỔ TỨC TIỀN MẶT + ROE + TĂNG TRƯỞNG
        if profit_growth_yoy >= 15: 
            fundamental_score += 20; fund_notes.append("LN tăng trưởng tốt")
        elif profit_growth_yoy >= 0:
            fundamental_score += 10; fund_notes.append("LN ổn định")

        if roe >= 15: 
            fundamental_score += 15; fund_notes.append("ROE sản xuất cao (>=15%)")
        elif roe >= 10:
            fundamental_score += 8; fund_notes.append("ROE khá")

        # Cổ tức tiền mặt là vua đối với nhóm sản xuất/tiêu dùng/điện/nước
        if dividend_yield >= 8.0:
            fundamental_score += 15; fund_notes.append(f"Cổ tức siêu khủng ({dividend_yield}%)")
        elif dividend_yield >= 5.0:
            fundamental_score += 10; fund_notes.append(f"Cổ tức tốt ({dividend_yield}%)")
        elif dividend_yield > 0:
            fundamental_score += 5; fund_notes.append(f"Có cổ tức ({dividend_yield}%)")

    # ==========================================
    # 2. CHẤM ĐIỂM KỸ THUẬT (20 điểm)
    # ==========================================
    technical_score = 0
    if "BREAKOUT" in recommendation or "CẠN CUNG" in recommendation or "MUA" in recommendation:
        technical_score += 20
    else:
        technical_score += 10

    # ==========================================
    # 3. ĐÁNH GIÁ ĐỊNH GIÁ AN TOÀN (30 điểm)
    # ==========================================
    valuation_score = 0
    if 0 < pe < 15 and 0 < pb < 2.5:
        valuation_score += 30
    elif 0 < pe < 22 and 0 < pb < 3.5:
        valuation_score += 18
    else:
        valuation_score += 5

    total_score = fundamental_score + technical_score + valuation_score

    potential_zone = "THEO DÕI THÊM"
    if total_score >= 75:
        potential_zone = "VÙNG TÍCH SẢN ĐẦU TƯ (A+)"
    elif total_score >= 60:
        potential_zone = "VÙNG MUA AN TOÀN (B)"

    return {
        "symbol": symbol,
        "sector": sector,
        "close_price": close_price,
        "pe": pe,
        "pb": pb,
        "roe": roe,
        "dividend_yield": dividend_yield,
        "net_profit_latest": net_profit,
        "profit_growth_yoy": profit_growth_yoy,
        "fundamental_score": fundamental_score,
        "technical_score": technical_score,
        "valuation_score": valuation_score,
        "total_score": total_score,
        "potential_zone": potential_zone,
        "technical_status": recommendation,
        "fundamental_notes": " | ".join(fund_notes)
    }

def main():
    print("🚀 Chạy bộ lọc định lượng thông minh (Tiêu chuẩn phân hóa theo từng nhóm ngành)...")
    
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
        return

    # Sắp xếp tổng thể để xuất file
    results = sorted(results, key=lambda x: (x.get('fundamental_score', 0), x.get('roe', 0)), reverse=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)
        
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    # In kết quả phân tách theo ngành rõ ràng
    industry_groups = {}
    for item in results:
        sec = item['sector']
        if sec not in industry_groups:
            industry_groups[sec] = []
        industry_groups[sec].append(item)

    for sector, items in industry_groups.items():
        limit_count = 5 if sector == "NGAN_HANG" else 3
        top_items = items[:limit_count]
        
        print(f"\n📌 NHÓM NGÀNH: [{sector}] - TOP {limit_count} TIÊU BIỂU:")
        print("=" * 115)
        df_sector = pd.DataFrame(top_items)
        print(df_sector[['symbol', 'dividend_yield', 'pe', 'roe', 'fundamental_score', 'total_score', 'potential_zone']].to_string(index=False))
        print("=" * 115)

if __name__ == "__main__":
    main()
