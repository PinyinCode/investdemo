import os
import time
import requests
import re
import json

SCREENER_FILE = "screener_results.json"
DATA_FILE = "data.json"

ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "").strip()
API_URL = "https://ws-8lcqaxwxdv0h9xzy.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"

# Phân nhóm ngành chuẩn cho VN100
SECTOR_MAPPING = {
    "NGAN_HANG": ["ACB", "BID", "CTG", "TCB", "MBB", "STB", "VPB", "HDB", "VIB", "TPB", "SHB", "SSB", "LPB", "MSB", "OCB", "EIB"],
    "CHUNG_KHOAN": ["SSI", "VCI", "HCM", "VIX", "MBS", "FTS", "BSI", "CTS", "ORS"],
    "BAT_DONG_SAN": ["VHM", "VIC", "VRE", "NVL", "PDR", "DIG", "NLG", "KDH", "CEO", "DXG", "TCH", "HDG", "KBC", "IDC", "SZC", "BCM", "PHR"],
    "SAN_XUAT_TIEU_DUNG": ["HPG", "HSG", "NKG", "CTD", "VCG", "HHV", "FPT", "MWG", "PNJ", "FRT", "VNM", "MSN", "SAB", "GAS", "PVD", "PVS", "BSR", "POW", "REE", "PC1", "NT2", "GMD", "HAH", "PVT", "VJC", "HVN", "VHC", "ANV"]
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

def analyze_stock_with_ai(item, sector):
    if not ALIBABA_API_KEY:
        print(f"❌ LỖI: Biến môi trường ALIBABA_API_KEY đang trống!")
        return None

    symbol = item.get('symbol')
    sector_guideline = get_sector_specific_guideline(sector)

    # Lấy toàn bộ chỉ số sạch từ screener_results.json
    close_price = item.get('close_price', 0)
    pe = item.get('pe', 0)
    pb = item.get('pb', 0)
    roe = item.get('roe', 0)
    eps = item.get('eps', 0)
    net_profit = item.get('net_profit_latest', 0)
    growth_yoy = item.get('profit_growth_yoy', 0)
    total_score = item.get('total_score', 0)
    tech_status = item.get('technical_status', 'Tích lũy')

    prompt = f"""
    Bạn là một Chuyên gia Phân tích Tài chính Cấp cao kiêm Quản lý Quỹ Đầu tư xuất sắc. 
    Hãy thực hiện một bản **đánh giá phân tích chuyên sâu theo ĐẶC THÙ NGÀNH ({sector})**, dựa trực tiếp trên các chỉ số tài chính định lượng của mã: {symbol}.

    --- DỮ LIỆU TÀI CHÍNH TỪ HỆ THỐNG SCREENER ---
    - Mã CK: {symbol} | Ngành: {sector} | Tổng điểm: {total_score}/100
    - Giá đóng cửa: {close_price:,.0f} VNĐ
    - Chỉ số định giá: P/E = {pe} | P/B = {pb}
    - Khả năng sinh lời: ROE = {roe}% | EPS = {eps:,.0f} VNĐ
    - Lợi nhuận mới nhất: {net_profit:,.0f} Tỷ VNĐ | Tăng trưởng lợi nhuận YoY = {growth_yoy}%
    - Trạng thái kỹ thuật: {tech_status}
    --------------------------------------------------------------

    {sector_guideline}

    YÊU CẦU TRẢ VỀ JSON THUẦN TÚY (TUYỆT ĐỐI KHÔNG DÙNG ```json):
    1. "bctc": Phân tích sâu sát về sức khỏe lợi nhuận, tốc độ tăng trưởng YoY và hiệu quả ROE (5-7 câu).
    2. "outlook": Đánh giá triển vọng định giá (P/E, P/B) và biên an toàn (4-6 câu).
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
    if not os.path.exists(SCREENER_FILE):
        print(f"❌ Không tìm thấy file {SCREENER_FILE}!")
        return

    with open(SCREENER_FILE, "r", encoding="utf-8") as f:
        screener_data = json.load(f)

    # 1. Gom nhóm ngành và LỌC RA TOP 3 MÃ CÓ TỔNG ĐIỂM CAO NHẤT MỖI NGÀNH
    industry_groups = {}
    for item in screener_data:
        symbol = item.get('symbol')
        if item.get('close_price', 0) <= 0:
            continue
        sector = get_sector(symbol)
        item['sector'] = sector
        if sector not in industry_groups:
            industry_groups[sector] = []
        industry_groups[sector].append(item)

    top_symbols_to_analyze = {}
    for sector, items in industry_groups.items():
        items_sorted = sorted(items, key=lambda x: (x.get('total_score', 0), x.get('roe', 0)), reverse=True)
        top_3 = items_sorted[:3] # Lấy chính xác Top 3 mỗi ngành
        for itm in top_3:
            top_symbols_to_analyze[itm['symbol']] = sector
        print(f"📌 Nhóm ngành [{sector}] - Top 3 phân tích AI: {[i['symbol'] for i in top_3]}")

    # Đọc data.json hiện tại để ghi đè kết quả phân tích AI vào
    stock_db = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            stock_db = json.load(f)

    print(f"\n🤖 Bắt đầu chạy phân tích CHỈ CHO CÁC MÃ TOP 3 từ screener_results.json...")
    count = 0
    
    for item in screener_data:
        symbol = item.get('symbol')
        if item.get('close_price', 0) <= 0:
            continue
            
        # Chỉ gọi AI nếu mã nằm trong Top 3
        if symbol in top_symbols_to_analyze:
            sector = top_symbols_to_analyze[symbol]
            
            if symbol not in stock_db:
                stock_db[symbol] = {}
                
            data_entry = stock_db[symbol]
            updated_at = data_entry.get("updated_at", "")
            ai_updated_at = data_entry.get("ai_updated_at", "")
            
            if not data_entry.get("ai_recommendation") or updated_at > ai_updated_at:
                print(f"🔍 [{sector}] Đang phân tích AI mã: {symbol}...")
                ai_result = analyze_stock_with_ai(item, sector)
                
                if ai_result:
                    # Ghi ngược kết quả phân tích AI vào data.json
                    data_entry["bctc"] = ai_result.get("bctc", "")
                    data_entry["outlook"] = ai_result.get("outlook", "")
                    data_entry["ai_recommendation"] = ai_result.get("recommendation", "")
                    data_entry["ai_price_zone"] = ai_result.get("price_zone", "")
                    data_entry["macro_view"] = ai_result.get("macro_view", "")
                    data_entry["ai_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    count += 1
                    print(f"  -> ✅ Ghi ngược thành công vào data.json cho {symbol}")
                else:
                    print(f"  -> ❌ Lỗi gọi AI cho {symbol}")
                
                time.sleep(1.5)
            else:
                print(f"💤 Bỏ qua {symbol} (Đã có phân tích AI mới nhất).")
        else:
            pass

    # Lưu lại file data.json sau khi đã cập nhật
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 Hoàn thành! Đã cập nhật phân tích AI cho {count} mã Top đầu và ghi ngược vào {DATA_FILE}.")

if __name__ == "__main__":
    main()
