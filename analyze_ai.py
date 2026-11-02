import os
import time
import requests
import re
import json

SCREENER_FILE = "screener_results.json"
DATA_FILE = "data.json"

ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "").strip()
INPUT_SYMBOLS = os.getenv("INPUT_SYMBOLS", "").strip()
API_URL = "https://ws-8lcqaxwxdv0h9xzy.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"

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

def get_sector_specific_guideline(sector):
    if sector == "NGAN_HANG":
        return "* ĐẶC THÙ NGÀNH NGÂN HÀNG: Tập trung phân tích tốc độ tăng trưởng tín dụng, hiệu quả sinh lời ROE và biên định giá P/B, P/E."
    elif sector == "CHUNG_KHOAN":
        return "* ĐẶC THÙ NGÀNH CHỨNG KHOÁN: Tập trung phân tích lợi nhuận ròng, tốc độ tăng trưởng YoY và độ nhạy thanh khoản thị trường."
    elif sector == "BAT_DONG_SAN":
        return "* ĐẶC THÙ NGÀNH BẤT ĐỘNG SẢN: Tập trung phân tích điểm rơi lợi nhuận (`net_profit_latest`), tăng trưởng YoY đột biến và định giá."
    else:
        return "* ĐẶC THÙ NGÀNH SẢN XUẤT/BÁN LẺ: Tập trung phân tích quy mô lợi nhuận, hiệu quả ROE và tốc độ phục hồi lợi nhuận kinh doanh."

def analyze_stock_with_ai(symbol, stock_metrics, screener_item, sector):
    if not ALIBABA_API_KEY:
        print(f"❌ LỖI: Biến môi trường ALIBABA_API_KEY đang trống!")
        return None

    sector_guideline = get_sector_specific_guideline(sector)

    close_price = stock_metrics.get('close', stock_metrics.get('close_price', 0))
    pe = stock_metrics.get('pe', 0)
    pb = stock_metrics.get('pb', 0)
    roe = stock_metrics.get('roe', 0)
    eps = stock_metrics.get('eps', 0)
    
    net_profit = screener_item.get('net_profit_latest', 0)
    growth_yoy = screener_item.get('profit_growth_yoy', 0)
    total_score = screener_item.get('total_score', 0)
    tech_status = screener_item.get('technical_status', 'Tích lũy')

    prompt = f"""
    Bạn là một Chuyên gia Phân tích Tài chính Cấp cao kiêm Quản lý Quỹ Đầu tư xuất sắc. 
    Hãy thực hiện một bản **đánh giá phân tích chuyên sâu theo ĐẶC THÙ NGÀNH ({sector})**, dựa trực tiếp trên các chỉ số tài chính định lượng của mã: {symbol}.

    --- DỮ LIỆU TÀI CHÍNH TỪ HỆ THỐNG ---
    - Mã CK: {symbol} | Ngành: {sector} | Tổng điểm: {total_score}/100
    - Giá đóng cửa: {close_price:,.0f} VNĐ
    - Chỉ số định giá (từ data.json): P/E = {pe} | P/B = {pb}
    - Khả năng sinh lời (từ data.json): ROE = {roe}% | EPS = {eps:,.0f} VNĐ
    - Dữ liệu BCTC & Tăng trưởng (từ screener): Lợi nhuận mới nhất = {net_profit:,.0f} Tỷ VNĐ | Tăng trưởng YoY = {growth_yoy}%
    - Trạng thái kỹ thuật: {tech_status}
    --------------------------------------------------------------

    {sector_guideline}

    YÊU CẦU TRẢ VỀ JSON THUẦN TÚY (TUYỆT ĐỐI KHÔNG DÙNG ```json):
    1. "bctc": Phân tích sâu sát về sức khỏe lợi nhuận, tốc độ tăng trưởng YoY, hiệu quả ROE và đánh giá mức EPS = {eps:,.0f} VNĐ (5-7 câu).
    2. "outlook": Đánh giá triển vọng định giá (P/E = {pe}, P/B = {pb}) và biên an toàn (4-6 câu).
    3. "recommendation": Khuyến nghị hành động sắc bén (Ngắn gọn 3-6 từ, ví dụ: "Tích sản dài hạn giá hấp dẫn").
    4. "price_zone": Vạch rõ chiến lược giá chi tiết (vùng gom, cắt lỗ, gia tăng tỷ trọng).
    5. "macro_view": Phân tích vĩ mô & triển vọng ngành liên hệ với số liệu doanh nghiệp (5-7 câu).

    BẮT BUỘC KHÓA JSON: "bctc", "outlook", "recommendation", "price_zone", "macro_view".
    """

    headers = {
        "Authorization": f"Bearer {ALIBABA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-max",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            content = res_json["choices"][0]["message"]["content"].strip()
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            return json.loads(content)
        else:
            print(f"[{symbol}] Lỗi HTTP {response.status_code}")
    except Exception as e:
        print(f"[{symbol}] Lỗi AI: {e}")
    
    return None

def main():
    if not os.path.exists(SCREENER_FILE) or not os.path.exists(DATA_FILE):
        print(f"❌ Không tìm thấy file dữ liệu đầu vào!")
        return

    with open(SCREENER_FILE, "r", encoding="utf-8") as f:
        screener_data = json.load(f)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    screener_map = {item.get('symbol'): item for item in screener_data if item.get('close_price', 0) > 0}

    top_symbols_to_analyze = {}

    # KIỂM TRA NẾU NGƯỜI DÙNG NHẬP TRỰC TIẾP CÁC MÃ QUA WORKFLOW INPUT
    if INPUT_SYMBOLS:
        custom_list = [s.strip().upper() for s in INPUT_SYMBOLS.split(",") if s.strip()]
        print(f"🎯 Phát hiện danh sách mã nhập thủ công: {custom_list}")
        for symbol in custom_list:
            if symbol in screener_map:
                top_symbols_to_analyze[symbol] = get_sector(symbol)
            else:
                print(f"⚠️ Mã {symbol} không có trong dữ liệu screener, bỏ qua.")
    else:
        # Mặc định: Ngân hàng lấy Top 5, các ngành khác lấy Top 3 theo điểm cơ bản
        industry_groups = {}
        for symbol, item in screener_map.items():
            sector = get_sector(symbol)
            item['sector'] = sector
            if sector not in industry_groups:
                industry_groups[sector] = []
            industry_groups[sector].append(item)

        for sector, items in industry_groups.items():
            items_sorted = sorted(
                items, 
                key=lambda x: (
                    x.get('fundamental_score', 0), 
                    x.get('roe', 0), 
                    x.get('net_profit_latest', 0),
                    x.get('total_score', 0)
                ), 
                reverse=True
            )
            limit_count = 5 if sector == "NGAN_HANG" else 3
            selected_items = items_sorted[:limit_count]
            for itm in selected_items:
                top_symbols_to_analyze[itm['symbol']] = sector
            print(f"📌 Nhóm ngành [{sector}] - Tự động chọn Top {limit_count}: {[i['symbol'] for i in selected_items]}")

    print(f"\n🤖 Bắt đầu chạy phân tích chuyên sâu cho các mã: {list(top_symbols_to_analyze.keys())}")
    count = 0
    
    for symbol, sector in top_symbols_to_analyze.items():
        if symbol not in stock_db:
            stock_db[symbol] = {}
        if symbol not in screener_map:
            continue
            
        stock_metrics = stock_db[symbol]
        screener_item = screener_map[symbol]
        
        print(f"🔍 [{sector}] Đang phân tích AI mã: {symbol}...")
        ai_result = analyze_stock_with_ai(symbol, stock_metrics, screener_item, sector)
        
        if ai_result:
            stock_metrics["bctc"] = ai_result.get("bctc", "")
            stock_metrics["outlook"] = ai_result.get("outlook", "")
            stock_metrics["ai_recommendation"] = ai_result.get("recommendation", "")
            stock_metrics["ai_price_zone"] = ai_result.get("price_zone", "")
            stock_metrics["macro_view"] = ai_result.get("macro_view", "")
            stock_metrics["ai_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            count += 1
            print(f"  -> ✅ Phân tích thành công cho {symbol}")
        else:
            print(f"  -> ❌ Lỗi gọi AI cho {symbol}")
        
        time.sleep(1.5)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 Hoàn thành! Đã cập nhật phân tích AI cho {count} mã và ghi vào {DATA_FILE}.")

if __name__ == "__main__":
    main()
