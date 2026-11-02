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
    price_zone = data.get("price_zone", "")
    close_price = data.get("close", 0)
    
    bctc_history = data.get("bctc_history", [])
    if not bctc_history:
        return None
        
    latest = bctc_history[0]
    net_profit = latest.get("net_profit", 0)
    profit_growth_yoy = latest.get("profit_growth_yoy", 0)
    credit_growth_yoy = latest.get("credit_growth_yoy", 0)

    # ==========================================
    # 1. CHẤM ĐIỂM PHÂN TÍCH CƠ BẢN & CỔ TỨC (Thang 50 điểm)
    # ==========================================
    fundamental_score = 0
    fund_notes = []

    if sector == "NGAN_HANG":
        if credit_growth_yoy >= 12: 
            fundamental_score += 15; fund_notes.append("Tín dụng tốt")
        if roe >= 16: 
            fundamental_score += 15; fund_notes.append("ROE cao (>16%)")
    else:
        if profit_growth_yoy >= 15: 
            fundamental_score += 15; fund_notes.append("LN tăng trưởng tốt")
        if roe >= 14: 
            fundamental_score += 15; fund_notes.append("ROE đạt chuẩn (>14%)")

    # Điểm cổ tức tiền mặt (Chất lượng dòng tiền)
    if dividend_yield >= 8.0:
        fundamental_score += 20
        fund_notes.append(f"Cổ tức siêu hấp dẫn ({dividend_yield}%)")
    elif dividend_yield >= 5.0:
        fundamental_score += 12
        fund_notes.append(f"Cổ tức tốt vượt tiết kiệm ({dividend_yield}%)")
    elif dividend_yield > 0:
        fundamental_score += 5
        fund_notes.append(f"Có chia cổ tức ({dividend_yield}%)")

    # ==========================================
    # 2. CHẤM ĐIỂM PHÂN TÍCH KỸ THUẬT (Thang 20 điểm)
    # ==========================================
    technical_score = 0
    tech_notes = []
    if "BREAKOUT" in recommendation or "CẠN CUNG" in recommendation:
        technical_score += 20
        tech_notes.append("Dòng tiền/Kỹ thuật thuận lợi")
    else:
        technical_score += 10
        tech_notes.append("Tích lũy nền dài")

    # ==========================================
    # 3. ĐÁNH GIÁ ĐỊNH GIÁ AN TOÀN (Thang 30 điểm)
    # ==========================================
    valuation_score = 0
    val_notes = []

    if 0 < pe < 14 and 0 < pb < 2.0:
        valuation_score += 30
        val_notes.append("Định giá rẻ, biên an toàn cao")
    elif 0 < pe < 20 and 0 < pb < 3.0:
        valuation_score += 18
        val_notes.append("Định giá hợp lý")
    else:
        valuation_score += 5
        val_notes.append("Định giá cao/Cần thận trọng")

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
        "price_zone_detail": price_zone,
        "fundamental_notes": " | ".join(fund_notes),
        "technical_notes": " | ".join(tech_notes),
        "valuation_notes": " | ".join(val_notes)
    }

def main():
    print("🚀 Chạy bộ lọc định lượng Đầu tư Giá trị & Cổ tức (Phân theo nhóm ngành)...")
    
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
        print("⚠️ Không có dữ liệu để đánh giá.")
        return

    # Sắp xếp toàn thị trường theo điểm cơ bản & cổ tức giảm dần
    results = sorted(
        results, 
        key=lambda x: (
            x.get('fundamental_score', 0), 
            x.get('dividend_yield', 0), 
            x.get('roe', 0)
        ), 
        reverse=True
    )

    # 1. Xuất file JSON & CSV
    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)
    print(f"✅ Đã xuất thành công: {OUTPUT_JSON}")
        
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Đã xuất thành công: {OUTPUT_CSV}")

    # 2. Hiển thị kết quả chi tiết chia theo từng nhóm ngành trên Console
    industry_groups = {}
    for item in results:
        sec = item['sector']
        if sec not in industry_groups:
            industry_groups[sec] = []
        industry_groups[sec].append(item)

    for sector, items in industry_groups.items():
        limit_count = 5 if sector == "NGAN_HANG" else 3
        top_items = items[:limit_count]
        
        print(f"\n📌 NHÓM NGÀNH: [{sector}] - TOP {limit_count} HÀNG ĐẦU:")
        print("=" * 115)
        df_sector = pd.DataFrame(top_items)
        print(df_sector[['symbol', 'dividend_yield', 'pe', 'roe', 'total_score', 'potential_zone']].to_string(index=False))
        print("=" * 115)

if __name__ == "__main__":
    main()
