import os
import json
import pandas as pd
import numpy as np
import datetime
import subprocess

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
    return "KHAC"

def evaluate_stock(symbol, data):
    sector = get_sector(symbol)
    pe = data.get("pe", 0)
    pb = data.get("pb", 0)
    roe = data.get("roe", 0)
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
    # 1. CHẤM ĐIỂM PHÂN TÍCH CƠ BẢN (PTCB - Thang 50 điểm)
    # ==========================================
    fundamental_score = 0
    fund_notes = []

    if sector == "NGAN_HANG":
        if credit_growth_yoy >= 15: 
            fundamental_score += 25; fund_notes.append("Tín dụng tăng trưởng mạnh (>15%)")
        elif credit_growth_yoy >= 10: 
            fundamental_score += 15; fund_notes.append("Tín dụng tăng trưởng khá")
        
        if roe >= 18: 
            fundamental_score += 25; fund_notes.append("ROE xuất sắc (>18%)")
        elif roe >= 14: 
            fundamental_score += 15; fund_notes.append("ROE tốt (>14%)")
        
    elif sector == "CHUNG_KHOAN":
        if profit_growth_yoy >= 40: 
            fundamental_score += 25; fund_notes.append("LNST bùng nổ mạnh (>40%)")
        elif profit_growth_yoy >= 20: 
            fundamental_score += 15; fund_notes.append("LNST tăng trưởng tốt")
        
        if roe >= 15: 
            fundamental_score += 25; fund_notes.append("ROE chứng khoán cao")
        elif roe >= 10: 
            fundamental_score += 15; fund_notes.append("ROE khá")
        
    elif sector == "BAT_DONG_SAN":
        if net_profit >= 200: 
            fundamental_score += 25; fund_notes.append("Điểm rơi lợi nhuận lớn (>200 tỷ)")
        elif net_profit >= 50: 
            fundamental_score += 15; fund_notes.append("Có ghi nhận lợi nhuận")
        
        if profit_growth_yoy >= 50: 
            fundamental_score += 25; fund_notes.append("Tăng trưởng YoY cực cao")
        elif profit_growth_yoy > 0: 
            fundamental_score += 15; fund_notes.append("Phục hồi YoY")
        
    else: # Sản xuất, Thép, Bán lẻ, Năng lượng...
        if profit_growth_yoy >= 30: 
            fundamental_score += 25; fund_notes.append("Tăng trưởng cốt lõi mạnh (>30%)")
        elif profit_growth_yoy >= 10: 
            fundamental_score += 15; fund_notes.append("Tăng trưởng ổn định")
        
        if roe >= 15: 
            fundamental_score += 25; fund_notes.append("Hiệu quả sinh lời ROE cao (>15%)")
        elif roe >= 10: 
            fundamental_score += 15; fund_notes.append("ROE đạt chuẩn")

    # ==========================================
    # 2. CHẤM ĐIỂM PHÂN TÍCH KỸ THUẬT (PTKT - Thang 30 điểm)
    # ==========================================
    technical_score = 0
    tech_notes = []

    if "BREAKOUT" in recommendation:
        technical_score += 30
        tech_notes.append("Dòng tiền bùng nổ (Breakout)")
    elif "CẠN CUNG" in recommendation:
        technical_score += 25
        tech_notes.append("Tích lũy cạn cung (Sẵn sàng đánh)")
    elif "GOM HÀNG" in recommendation:
        technical_score += 20
        tech_notes.append("Dòng tiền gom hàng ổn định trên MA20")
    else:
        technical_score += 10
        tech_notes.append("Đang tích lũy nền")

    # ==========================================
    # 3. ĐÁNH GIÁ ĐỊNH GIÁ & VÙNG GIÁ TIỀM NĂNG (Thang 20 điểm)
    # ==========================================
    valuation_score = 0
    val_notes = []

    if 0 < pe < 15 and 0 < pb < 2.5:
        valuation_score += 20
        val_notes.append("Định giá hấp dẫn (P/E & P/B thấp)")
    elif 0 < pe < 22 and 0 < pb < 3.5:
        valuation_score += 12
        val_notes.append("Định giá hợp lý")
    else:
        valuation_score += 5
        val_notes.append("Định giá cao/Cần thận trọng")

    # Tổng điểm tổng hợp (Max 100 điểm)
    total_score = fundamental_score + technical_score + valuation_score

    # Xác định trạng thái Vùng giá tiềm năng
    potential_zone = "THEO DÕI THÊM"
    if total_score >= 75:
        potential_zone = "VÙNG MUA MẠNH (A+)"
    elif total_score >= 60:
        potential_zone = "VÙNG TIỀM NĂNG (B)"

    return {
        "symbol": symbol,
        "sector": sector,
        "close_price": close_price,
        "pe": pe,
        "pb": pb,
        "roe": roe,
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

def auto_git_push():
    """Tự động commit và push file kết quả lên GitHub"""
    try:
        print("\n📤 Đang tiến hành đồng bộ kết quả lên GitHub...")
        subprocess.run(["git", "add", OUTPUT_JSON, OUTPUT_CSV], check=True)
        commit_msg = f"Auto update quant screener evaluation results - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Đẩy kết quả lọc lên GitHub thành công!")
    except subprocess.CalledProcessError:
        print("⚠️ Git: Không có thay đổi mới để push hoặc đã được cập nhật.")
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

def main():
    print("🚀 Bắt đầu chạy bộ lọc định lượng chuyên sâu (Advanced Quant Screener) cho VN100...")
    
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
        print("⚠️ Không có dữ liệu đánh giá.")
        return

    # SẮP XẾP ƯU TIÊN TUYỆT ĐỐI THEO CHẤT LƯỢNG CƠ BẢN:
    results = sorted(
        results, 
        key=lambda x: (
            x.get('fundamental_score', 0), 
            x.get('roe', 0), 
            x.get('net_profit_latest', 0), 
            x.get('total_score', 0)
        ), 
        reverse=True
    )

    # 1. Xuất file JSON riêng cho Frontend HTML/JS
    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=4)
    print(f"✅ Đã xuất file JSON thành công: {OUTPUT_JSON}")

    # 2. Xuất file CSV tổng hợp báo cáo
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Đã xuất file CSV thành công: {OUTPUT_CSV}")

    # In mẫu Top 10 mã cơ bản mạnh nhất ra màn hình console
    print("\n🏆 TOP 10 CỔ PHIẾU CƠ BẢN TỐT NHẤT TOÀN THỊ TRƯỜNG:")
    print("=" * 125)
    print(df[['symbol', 'sector', 'fundamental_score', 'roe', 'net_profit_latest', 'total_score', 'potential_zone']].head(10).to_string(index=False))
    print("=" * 125)

    # Tự động đẩy lên git
    auto_git_push()

if __name__ == "__main__":
    main()
