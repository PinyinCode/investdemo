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

# Phân nhóm ngành chuẩn chi tiết cho 7 nhóm ngành VN100
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
    "CONG_NGHE_BAN_LE": [
        "FPT", "MWG", "PNJ", "FRT", "DGW"
    ],
    "DIEN_NUOC_HA_TANG": [
        "POW", "REE", "PC1", "NT2", "GAS", "GEG", "BWE", "TDM"
    ],
    "NGUYEN_VAT_LIEU_CHU_KY": [
        "HPG", "HSG", "NKG", "DGC", "DCM", "DPM", "GVR", "PHR", "DHC"
    ],
    "SAN_XUAT_TIEU_DUNG_PHONG_THU": [
        "VNM", "MSN", "SAB", "VHC", "ANV", "BVH", "PLX", "PVD", "PVS", "BSR", 
        "GMD", "HAH", "PVT", "VJC", "HVN", "APH", "ASM", "DBC", "KDC", "MSH", 
        "PAN", "SBT", "DRC", "CSM", "BMP", "DHG", "CTD", "VCG", "HHV", "GEX"
    ]
}

def get_sector(symbol):
    for sector, symbols in SECTOR_MAPPING.items():
        if symbol in symbols:
            return sector
    return "SAN_XUAT_TIEU_DUNG_PHONG_THU"

def analyze_stock_with_ai(symbol, stock_metrics, screener_item, sector):
    if not ALIBABA_API_KEY:
        print(f"❌ LỖI: Biến môi trường ALIBABA_API_KEY đang trống!")
        return None

    close_price = stock_metrics.get('close', stock_metrics.get('close_price', 0))
    pe = stock_metrics.get('pe', 0)
    pb = stock_metrics.get('pb', 0)
    roe = stock_metrics.get('roe', 0)
    eps = stock_metrics.get('eps', 0)
    dividend_yield = stock_metrics.get('dividend_yield', 0)
    
    net_profit = screener_item.get('net_profit_latest', 0)
    growth_yoy = screener_item.get('profit_growth_yoy', 0)
    total_score = screener_item.get('total_score', 0)
    fund_notes = screener_item.get('fundamental_notes', '')

    # Xây dựng hướng dẫn riêng cho AI tùy theo đặc thù từng nhóm ngành
    sector_guidance = ""
    if sector == "NGAN_HANG":
        sector_guidance = "Đặc thù ngành Ngân hàng: Tập trung đánh giá chất lượng tài sản, tăng trưởng tín dụng, biên lãi ròng (NIM) và ROE. Lưu ý chính sách cổ tức bằng cổ phiếu/giữ vốn để tăng trưởng thay vì đòi hỏi cổ tức tiền mặt cao."
    elif sector == "CHUNG_KHOAN":
        sector_guidance = "Đặc thù ngành Chứng khoán: Nhạy bén theo chu kỳ thanh khoản thị trường, mảng tự doanh, cho vay margin và doanh thu môi giới. Đánh giá khả năng quản trị rủi ro danh mục."
    elif sector == "BAT_DONG_SAN":
        sector_guidance = "Đặc thù ngành Bất động sản: Đánh giá quỹ đất sạch, năng lực pháp lý dự án, người mua trả tiền trước và cơ cấu nợ vay/đòn bẩy tài chính thay vì chỉ nhìn P/E ngắn hạn."
    elif sector == "CONG_NGHE_BAN_LE":
        sector_guidance = "Đặc thù ngành Công nghệ & Bán lẻ: Trọng tâm là tốc độ tăng trưởng doanh thu cốt lõi, thị phần, biên lợi nhuận và tiềm năng mở rộng quy mô (Scalability)."
    elif sector == "DIEN_NUOC_HA_TANG":
        sector_guidance = "Đặc thù ngành Tiện ích/Hạ tầng: Dòng tiền phòng thủ ổn định, ít rủi ro suy thoái kinh tế. Trọng tâm đánh giá tính đều đặn của cổ tức tiền mặt và dòng tiền kinh doanh cốt lõi (CFO)."
    elif sector == "NGUYEN_VAT_LIEU_CHU_KY":
        sector_guidance = "Đặc thù ngành Vật liệu chu kỳ (Thép, Hóa chất...): Nhìn nhận qua góc độ chu kỳ giá hàng hóa (commodity cycle), P/B, biên lợi nhuận gộp theo từng quý thay vì bẫy P/E thấp ở đỉnh lợi nhuận."
    else:
        sector_guidance = "Đặc thù ngành Sản xuất & Tiêu dùng: Đánh giá sức khỏe thương hiệu (Economic Moat), thị phần nội địa, hiệu quả chuỗi cung ứng và lịch sử chi trả cổ tức tiền mặt đều đặn."

    prompt = f"""
    Bạn là một Chuyên gia Đầu tư Giá trị & Tăng trưởng kỳ cựu theo trường phái Graham, Buffett & Fisher. 
    Hãy thực hiện một bản **đánh giá tích sản dài hạn chuyên sâu** cho mã cổ phiếu: {symbol} thuộc nhóm ngành: {sector}.

    --- ĐẶC THÙ NGÀNH ---
    {sector_guidance}

    --- DỮ LIỆU TÀI CHÍNH & ĐỊNH LƯỢNG ---
    - Mã CK: {symbol} | Điểm chất lượng ngành: {total_score}/100 ({fund_notes})
    - Giá thị trường: {close_price:,.0f} VNĐ
    - Định giá: P/E = {pe} | P/B = {pb}
    - Cổ tức & Sinh lời: Tỷ suất cổ tức gần nhất = {dividend_yield}%/năm | ROE = {roe}% | EPS = {eps:,.0f} VNĐ
    - Tăng trưởng gần nhất: LNST = {net_profit:,.0f} Tỷ | Tăng trưởng YoY = {growth_yoy}%
    --------------------------------------------------------------

    YÊU CẦU TRẢ VỀ JSON THUẦN TÚY (TUYỆT ĐỐI KHÔNG DÙNG ```json):
    1. "bctc": Phân tích sức khỏe tài chính cốt lõi, đánh giá hiệu quả sinh lời và tính bền vững của dòng tiền/cổ tức phù hợp với đặc thù ngành (6-8 câu).
    2. "catalyst": Xác định lợi thế cạnh tranh dài hạn (Economic Moat) và động lực tăng trưởng nội tại trong 2-3 năm tới (4-5 câu).
    3. "risks": Chỉ ra các rủi ro trọng yếu có thể làm xói mòn giá trị doanh nghiệp hoặc đe dọa triển vọng kinh doanh (3-4 câu).
    4. "outlook": Đánh giá biên an toàn (Margin of Safety) của mức định giá hiện tại (P/E {pe}, P/B {pb}) dưới góc nhìn đầu tư dài hạn (4-5 câu).
    5. "recommendation": Khuyến nghị hành động tích sản sắc bén (Ví dụ: "Tích sản dài hạn - Tỷ trọng 20%").
    6. "price_zone": Vạch rõ chiến lược tích sản dạng văn bản liền mạch (Ví dụ: "Vùng gom giá trị: dưới 20k, Vùng chặn lỗ: thủng 18k, Kỳ vọng dài hạn: tăng trưởng 25%"). TUYỆT ĐỐI KHÔNG TRẢ VỀ DẠNG DICTIONARY/OBJECT.
    7. "macro_view": Phân tích chu kỳ ngành và vĩ mô tác động đến dòng tiền của doanh nghiệp (5-6 câu).

    BẮT BUỘC KHÓA JSON: "bctc", "catalyst", "risks", "outlook", "recommendation", "price_zone", "macro_view".
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
            
            parsed_data = json.loads(content)
            
            # 🛡️ BỔ SUNG BƯỚC AN TOÀN: Chuẩn hóa price_zone luôn là chuỗi string
            raw_pz = parsed_data.get("price_zone", "")
            if isinstance(raw_pz, dict):
                parsed_data["price_zone"] = " | ".join([f"{k}: {v}" for k, v in raw_pz.items()])
            elif isinstance(raw_pz, list):
                parsed_data["price_zone"] = " - ".join([str(i) for i in raw_pz])
            else:
                parsed_data["price_zone"] = str(raw_pz)
                
            return parsed_data
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

    if INPUT_SYMBOLS:
        custom_list = [s.strip().upper() for s in INPUT_SYMBOLS.split(",") if s.strip()]
        print(f"🎯 Phát hiện danh sách mã nhập thủ công: {custom_list}")
        for symbol in custom_list:
            if symbol in screener_map:
                top_symbols_to_analyze[symbol] = get_sector(symbol)
            else:
                print(f"⚠️ Mã {symbol} không có trong dữ liệu screener, bỏ qua.")
    else:
        # Gom nhóm và phân bổ: Tất cả 7 nhóm ngành đều lấy Top 5 tiêu biểu nhất
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
                    x.get('dividend_yield', 0), 
                    x.get('roe', 0)
                ), 
                reverse=True
            )
            limit_count = 5  # Đồng loạt lấy Top 5 cho tất cả các nhóm ngành
            selected_items = items_sorted[:limit_count]
            for itm in selected_items:
                top_symbols_to_analyze[itm['symbol']] = sector
            print(f"📌 Nhóm ngành [{sector}] - Chọn Top {limit_count}: {[i['symbol'] for i in selected_items]}")

    print(f"\n🤖 Bắt đầu chạy AI phân tích tích sản cho các mã: {list(top_symbols_to_analyze.keys())}")
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
            stock_metrics["catalyst"] = ai_result.get("catalyst", "")
            stock_metrics["risks"] = ai_result.get("risks", "")
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
        
    print(f"\n🎉 Hoàn thành! Đã cập nhật phân tích AI tích sản cho {count} mã theo đặc thù 7 nhóm ngành và ghi vào {DATA_FILE}.")

if __name__ == "__main__":
    main()
