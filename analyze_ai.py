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

# Phân nhóm ngành chuẩn chi tiết cho 7 nhóm ngành VN100 (Mỗi nhóm lấy Top 5)
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

    # Lấy các thông số cũ
    close_price = stock_metrics.get('close', stock_metrics.get('close_price', 0))
    pe = stock_metrics.get('pe', 0)
    pb = stock_metrics.get('pb', 0)
    roe = stock_metrics.get('roe', 0)
    eps = stock_metrics.get('eps', 0)
    dividend_yield = stock_metrics.get('dividend_yield', 0)
    
    # Lấy các thông số mới bổ sung từ chuỗi BCTC & Crawler nâng cao
    roa = stock_metrics.get('roa', 0)
    cfo_latest = stock_metrics.get('cfo_latest', 0)
    debt_to_equity = stock_metrics.get('debt_to_equity', 0)
    gross_margin = stock_metrics.get('gross_margin', 0)
    net_profit_ttm = stock_metrics.get('net_profit_ttm', 0)

    growth_yoy = screener_item.get('profit_growth_yoy', 0)
    total_score = screener_item.get('total_score', 0)
    fund_notes = screener_item.get('fundamental_notes', '')

    sector_guidance = ""
    if sector == "NGAN_HANG":
        sector_guidance = "Đặc thù ngành Ngân hàng: Trọng tâm đánh giá chất lượng tài sản, tăng trưởng tín dụng, biên lãi ròng (NIM), tỷ lệ bao phủ nợ xấu và cặp chỉ số ROE/ROA dưới đòn bẩy vốn đặc thù. Lưu ý chính sách giữ vốn thay vì cổ tức tiền mặt cao."
    elif sector == "CHUNG_KHOAN":
        sector_guidance = "Đặc thù ngành Chứng khoán: Nhạy bén theo thanh khoản thị trường, mảng tự doanh, cho vay margin và doanh thu môi giới. Đánh giá hệ số sinh lời tài sản (ROA) và hiệu quả quản trị rủi ro danh mục."
    elif sector == "BAT_DONG_SAN":
        sector_guidance = "Đặc thù ngành Bất động sản: Thẩm định quỹ đất sạch, pháp lý dự án, người mua trả tiền trước, cơ cấu nợ vay/đòn bẩy (D/E) và dòng tiền thuần từ hoạt động kinh doanh (CFO) thay vì chỉ nhìn P/E ngắn hạn."
    elif sector == "CONG_NGHE_BAN_LE":
        sector_guidance = "Đặc thù ngành Công nghệ & Bán lẻ: Trọng tâm là tốc độ tăng trưởng doanh thu cốt lõi, biên lợi nhuận gộp, vòng quay tài sản (ROA) và năng lực tối ưu hóa chi phí vận hành."
    elif sector == "DIEN_NUOC_HA_TANG":
        sector_guidance = "Đặc thù ngành Tiện ích/Hạ tầng: Dòng tiền phòng thủ ổn định, khấu hao tài sản cố định lớn. Trọng tâm đánh giá tính đều đặn của cổ tức tiền mặt và dòng tiền kinh doanh (CFO) thực tế."
    elif sector == "NGUYEN_VAT_LIEU_CHU_KY":
        sector_guidance = "Đặc thù ngành Vật liệu chu kỳ (Thép, Hóa chất...): Nhìn nhận qua góc độ chu kỳ giá hàng hóa (commodity cycle), biên lợi nhuận gộp theo từng quý và định giá P/B tại đỉnh/đáy chu kỳ."
    else:
        sector_guidance = "Đặc thù ngành Sản xuất & Tiêu dùng: Đánh giá sức mạnh thương hiệu (Economic Moat), thị phần, hiệu quả chuỗi cung ứng (phản ánh qua ROA) và lịch sử chi trả cổ tức tiền mặt."

    prompt = f"""
    Bạn là một Chuyên gia Đầu tư Giá trị & Tăng trưởng kỳ cựu theo trường phái Graham, Buffett & Fisher. 
    Hãy thực hiện một bản **đánh giá tích sản dài hạn chuyên sâu, khắt khe và đa chiều** cho mã cổ phiếu: {symbol} thuộc nhóm ngành: {sector}.

    --- ĐẶC THÙ NGÀNH ---
    {sector_guidance}

    --- DỮ LIỆU TÀI CHÍNH & ĐỊNH LƯỢNG (CŨ & MỚI) ---
    - Mã CK: {symbol} | Điểm chất lượng tổng hợp: {total_score}/100 ({fund_notes})
    - Giá thị trường: {close_price:,.0f} VNĐ
    - Định giá: P/E = {pe} | P/B = {pb}
    - Hiệu quả sinh lời: ROE = {roe}% | ROA = {roa}% | EPS = {eps:,.0f} VNĐ | Cổ tức = {dividend_yield}%/năm
    - Sức khỏe dòng tiền & Cấu trúc nợ: Lợi nhuận trượt 4 quý (TTM) = {net_profit_ttm:,.0f} Tỷ | Dòng tiền kinh doanh (CFO) = {cfo_latest:,.0f} Tỷ | Tỷ lệ Nợ/VCSH (D/E) = {debt_to_equity} | Biên lợi nhuận gộp = {gross_margin}%
    - Tăng trưởng gần nhất: Tăng trưởng LNST YoY = {growth_yoy}%
    --------------------------------------------------------------------------------------------------------------------------------

    YÊU CẦU TRẢ VỀ JSON THUẦN TÚY (TUYỆT ĐỐI KHÔNG DÙNG ```json):
    1. "bctc": [MỤC TRỌNG TÂM - PHÂN TÍCH SỨC KHỎE TÀI CHÍNH]: Phân tích cực kỳ chuyên sâu và chi tiết về bức tranh BCTC dựa trên các số liệu thực tế được cung cấp. Bắt buộc làm rõ mối quan hệ giữa Lợi nhuận TTM ({net_profit_ttm:,.0f} Tỷ) và Dòng tiền thuần từ hoạt động kinh doanh (CFO = {cfo_latest:,.0f} Tỷ) xem dòng tiền có thực sự thu về tiền mặt hay chỉ là "lợi nhuận trên giấy". Đánh giá hiệu suất sinh lời qua biên lợi nhuận gộp ({gross_margin}%), ROA ({roa}%), ROE ({roe}%) và gánh nặng đòn bẩy tài chính thông qua tỷ lệ Nợ trên vốn chủ sở hữu (D/E = {debt_to_equity}) (8-10 câu).
    2. "catalyst": Xác định lợi thế cạnh tranh dài hạn (Economic Moat) và động lực tăng trưởng nội tại trong 2-3 năm tới (4-5 câu).
    3. "risks": Chỉ trích thẳng thắn các rủi ro trọng yếu (Rủi ro chu kỳ, rủi ro đòn bẩy tài chính cao, rủi ro suy giảm biên lợi nhuận hoặc dòng tiền âm) có thể làm xói mòn giá trị doanh nghiệp (3-4 câu).
    4. "outlook": Đánh giá biên an toàn (Margin of Safety) của mức định giá hiện tại (P/E {pe}, P/B {pb}) kết hợp triển vọng dài hạn (4-5 câu).
    5. "recommendation": Khuyến nghị hành động tích sản sắc bén kèm tỷ trọng giải ngân (Ví dụ: "Tích sản dài hạn - Tỷ trọng 15-20%").
    6. "price_zone": Vạch rõ chiến lược tích sản dạng văn bản liền mạch (Ví dụ: "Vùng gom giá trị: dưới 20k, Vùng chặn lỗ: thủng 18k, Kỳ vọng dài hạn: tăng trưởng 25%"). TUYỆT ĐỐI KHÔNG TRẢ VỀ DẠNG DICTIONARY/OBJECT.
    7. "macro_view": Phân tích chu kỳ ngành và vĩ mô tác động đến dòng tiền kinh doanh của doanh nghiệp (5-6 câu).

    BẮT BUỘC KHÓA JSON ĐẦY ĐỦ: "bctc", "catalyst", "risks", "outlook", "recommendation", "price_zone", "macro_view".
    """

    headers = {
        "Authorization": f"Bearer {ALIBABA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen3.7-max",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    timeout_seconds = 120
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout_seconds)
            if response.status_code == 200:
                res_json = response.json()
                content = res_json["choices"][0]["message"]["content"].strip()
                content = re.sub(r"^```json\s*", "", content)
                content = re.sub(r"^```\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
                
                parsed_data = json.loads(content)
                
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
                break
        except requests.exceptions.Timeout:
            print(f"[{symbol}] ⏳ Lần thử {attempt + 1}/{max_retries} bị quá thời gian (Timeout), đang thử lại...")
            time.sleep(3)
        except Exception as e:
            print(f"[{symbol}] Lỗi AI: {e}")
            break
            
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
            limit_count = 5
            selected_items = items_sorted[:limit_count]
            for itm in selected_items:
                top_symbols_to_analyze[itm['symbol']] = sector
            print(f"📌 Nhóm ngành [{sector}] - Chọn Top {limit_count}: {[i['symbol'] for i in selected_items]}")

    print(f"\n🤖 Bắt đầu chạy AI phân tích tích sản chuyên sâu cho các mã: {list(top_symbols_to_analyze.keys())}")
    count = 0
    
    for symbol, sector in top_symbols_to_analyze.items():
        if symbol not in stock_db:
            stock_db[symbol] = {}
        if symbol not in screener_map:
            continue
            
        stock_metrics = stock_db[symbol]
        screener_item = screener_map[symbol]
        
        print(f"🔍 [{sector}] Đang phân tích AI chuyên sâu mã: {symbol}...")
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
        
        time.sleep(3)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 Hoàn thành! Đã cập nhật phân tích AI tích sản chuyên sâu cho {count} mã và ghi vào {DATA_FILE}.")

if __name__ == "__main__":
    main()
