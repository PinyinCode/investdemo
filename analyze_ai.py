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

    prompt = f"""
    Bạn là một Chuyên gia Đầu tư Giá trị (Value & Dividend Investor) kỳ cựu theo trường phái Graham & Buffett. 
    Hãy thực hiện một bản **đánh giá tích sản dài hạn chuyên sâu** cho mã cổ phiếu: {symbol} thuộc ngành {sector}.

    --- DỮ LIỆU TÀI CHÍNH & ĐỊNH LƯỢNG ---
    - Mã CK: {symbol} | Điểm chất lượng: {total_score}/100 ({fund_notes})
    - Giá thị trường: {close_price:,.0f} VNĐ
    - Định giá: P/E = {pe} | P/B = {pb}
    - Cổ tức & Sinh lời: Tỷ suất cổ tức gần nhất = {dividend_yield}%/năm | ROE = {roe}% | EPS = {eps:,.0f} VNĐ
    - Tăng trưởng gần nhất: LNST = {net_profit:,.0f} Tỷ | Tăng trưởng YoY = {growth_yoy}%
    --------------------------------------------------------------

    * LƯU Ý QUAN TRỌNG VỀ CỔ TỨC: Dữ liệu hệ thống hiện ghi nhận tỷ suất cổ tức năm gần nhất là {dividend_yield}%. Hãy dùng chuyên môn tài chính để phân tích xem mức cổ tức này có tính **bền vững dài hạn** hay chỉ là **đột biến một lần** (như bán tài sản, hoàn nhập dự phòng, hoặc lợi nhuận bất thường), dựa trên bối cảnh ngành và kết quả kinh doanh cốt lõi của doanh nghiệp. Tránh mắc bẫy cổ tức (dividend trap).

    YÊU CẦU TRẢ VỀ JSON THUẦN TÚY (TUYỆT ĐỐI KHÔNG DÙNG ```json):
    1. "bctc": Phân tích sức khỏe tài chính cốt lõi, đánh giá tính bền vững của mức cổ tức {dividend_yield}% (có đều đặn từ kinh doanh thực hay chỉ là đột biến một lần?) (6-8 câu).
    2. "catalyst": Xác định lợi thế cạnh tranh dài hạn (Economic Moat) và động lực tăng trưởng nội tại trong 2-3 năm tới (4-5 câu).
    3. "risks": Chỉ ra các rủi ro trọng yếu có thể làm xói mòn giá trị doanh nghiệp hoặc đe dọa chính sách cổ tức (3-4 câu).
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
                # Nếu AI lỡ trả về object, gom các giá trị lại thành chuỗi văn bản
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
        # Gom nhóm và phân bổ: Ngân hàng lấy Top 5, các ngành khác lấy Top 3
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
            limit_count = 5 if sector == "NGAN_HANG" else 3
            selected_items = items_sorted[:limit_count]
            for itm in selected_items:
                top_symbols_to_analyze[itm['symbol']] = sector
            print(f"📌 Nhóm ngành [{sector}] - Chọn Top {limit_count}: {[i['symbol'] for i in selected_items]}")

    print(f"\n🤖 Bắt đầu chạy AI phân tích tích sản giá trị cho các mã: {list(top_symbols_to_analyze.keys())}")
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
        
    print(f"\n🎉 Hoàn thành! Đã cập nhật phân tích AI tích sản cho {count} mã theo đúng định mức ngành và ghi vào {DATA_FILE}.")

if __name__ == "__main__":
    main()
