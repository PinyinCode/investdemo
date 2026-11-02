import os
import time
import requests
import re
import json

DATA_FILE = "data.json"
BCTC_DIR = "bctc_data"  # Thư mục chứa file JSON BCTC chi tiết

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
    return "SAN_XUAT_TIEU_DUNG" # Mặc định

def load_bctc_summary(symbol):
    file_path = os.path.join(BCTC_DIR, f"{symbol}.json")
    if not os.path.exists(file_path):
        return "Không có dữ liệu BCTC chi tiết."
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            bctc_raw = json.load(f)
            
        summary_info = []
        if 'income_statement' in bctc_raw:
            inc_data = bctc_raw['income_statement']
            if isinstance(inc_data, list) and len(inc_data) > 0:
                summary_info.append("--- KẾT QUẢ KINH DOANH 4 QUÝ GẦN NHẤT ---")
                for item in inc_data[:4]:
                    period = item.get('period', 'N/A')
                    rev = item.get('revenue', item.get('netRevenue', 0))
                    profit = item.get('profitAfterTax', item.get('netProfit', 0))
                    summary_info.append(f"Kỳ {period}: Doanh thu/Thu nhập lãi thuần = {rev:,.0f}, Lợi nhuận sau thuế = {profit:,.0f}")

        if 'balance_sheet' in bctc_raw:
            bal_data = bctc_raw['balance_sheet']
            if isinstance(bal_data, list) and len(bal_data) > 0:
                summary_info.append("--- CÂN ĐỐI KẾ TOÁN QUÝ MỚI NHẤT (CHỈ TIÊU CỐT LÕI) ---")
                latest = bal_data[0]
                for k, v in list(latest.items())[:15]:
                    summary_info.append(f"- {k}: {v}")

        return "\n".join(summary_info) if summary_info else "Dữ liệu BCTC trống."
    except Exception as e:
        return f"Lỗi đọc file BCTC: {e}"

def get_sector_specific_guideline(sector):
    """Định nghĩa tiêu chí bóc tách chuyên biệt riêng cho từng nhóm ngành"""
    if sector == "NGAN_HANG":
        return """
        * ĐẶC THÙ NGÀNH NGÂN HÀNG: Tập trung phân tích tốc độ tăng trưởng tín dụng, biên lãi ròng (NIM), chất lượng tài sản (tỷ lệ nợ xấu NPL, tỷ lệ bao phủ nợ xấu LLR), và tỷ lệ vốn ngắn hạn cho vay trung dài hạn. Đánh giá xem chi phí dự phòng rủi ro tín dụng có đang ăn mòn lợi nhuận hay không.
        """
    elif sector == "CHUNG_KHOAN":
        return """
        * ĐẶC THÙ NGÀNH CHỨNG KHOÁN: Tập trung phân tích quy mô cho vay Margin (dư nợ cho vay giao dịch ký quỹ), hiệu quả danh mục đầu tư tự doanh (FVTPL), và thị phần môi giới. Đánh giá độ nhạy của doanh thu trước biến động thanh khoản thị trường chung.
        """
    elif sector == "BAT_DONG_SAN":
        return """
        * ĐẶC THÙ NGÀNH BẤT ĐỘNG SẢN & HẠ TẦNG: Tập trung phân tích khoản "Người mua trả tiền trước" / "Doanh thu chưa thực hiện" (tiền khách hàng đặt cọc dự án), quy mô hàng tồn kho (dự án dở dang), áp lực nợ vay trái phiếu và khả năng tất toán nợ.
        """
    else:
        return """
        * ĐẶC THÙ NGÀNH SẢN XUẤT / BÁN LẺ / NĂNG LƯỢNG: Tập trung phân tích biên lợi nhuận gộp, vòng quay hàng tồn kho (rủi ro trích lập dự phòng giá vốn), đòn bẩy tài chính (tỷ lệ Nợ vay/Vốn chủ sở hữu) và dòng tiền thuần từ hoạt động kinh doanh (CFO) có thực sự dương và đều đặn không.
        """

def analyze_stock_with_ai(symbol, data, sector):
    if not ALIBABA_API_KEY:
        print(f"❌ LỖI: Biến môi trường ALIBABA_API_KEY đang trống!")
        return None

    bctc_text = load_bctc_summary(symbol)
    sector_guideline = get_sector_specific_guideline(sector)

    prompt = f"""
    Bạn là một Chuyên gia Phân tích Tài chính Cấp cao kiêm Quản lý Quỹ Đầu tư (Portfolio Manager) xuất sắc. 
    Hãy thực hiện một bản **đánh giá phân tích chiến lược chuyên sâu theo đúng ĐẶC THÙ NGÀNH ({sector})**, kết hợp chặt chẽ giữa chỉ số định lượng và số liệu BCTC của mã cổ phiếu: {symbol}.

    --- 1. CÁC CHỈ SỐ ĐỊNH LƯỢNG & THỊ TRƯỜNG ---
    - Ngành: {sector} | Giá: {data.get('close', 0):,.0f} VNĐ | Khối lượng: {data.get('volume', 0):,}
    - Định giá: P/E = {data.get('pe', 0)} | P/B = {data.get('pb', 0)}
    - Hiệu quả sinh lời: EPS = {data.get('eps', 0):,} VNĐ | ROE = {data.get('roe', 0)}% | ROA = {data.get('roa', 0)}% | Cổ tức = {data.get('dividend_yield', 0)}%
    - Trạng thái kỹ thuật: {data.get('recommendation', 'Chưa xác định')} | Vùng giá thô: {data.get('price_zone', 'Chưa có')}

    --- 2. DỮ LIỆU BÁO CÁO TÀI CHÍNH (BCTC) THỰC TẾ ---
    {bctc_text}
    -----------------------------------------------------------------

    {sector_guideline}

    YÊU CẦU TRẢ VỀ BẢN PHÂN TÍCH CHI TIẾT (Dạng JSON thuần túy, TUYỆT ĐỐI KHÔNG dùng định dạng markdown như ```json):
    1. "bctc": **Phân tích sâu sát theo đặc thù ngành (Từ 5-7 câu):** Đánh giá các chỉ số cốt lõi riêng của ngành ({sector}) trích xuất từ BCTC quý gần nhất.
    2. "outlook": **Đánh giá triển vọng định giá và biên an toàn (Từ 4-6 câu):** Phân tích P/E, P/B có hợp lý so với triển vọng ngành không.
    3. "recommendation": **Khuyến nghị hành động sắc bén (Ngắn gọn từ 3-6 từ):** Ví dụ: "Tích sản dài hạn giá hấp dẫn", "Định giá cao - Chờ chiết khấu".
    4. "price_zone": **Vạch rõ chiến lược giá chi tiết:** Vùng giá gom hợp lý, mốc cắt lỗ hoặc gia tăng tỷ trọng.
    5. "macro_view": **Phân tích vĩ mô & triển vọng ngành (Từ 5-7 câu):** Đan xen bức tranh vĩ mô với năng lực cạnh tranh thực tế của doanh nghiệp.

    BẮT BUỘC TRẢ VỀ ĐỐI TƯỢNG JSON THUẦN TÚY với các khóa chính xác: "bctc", "outlook", "recommendation", "price_zone", "macro_view".
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
            print(f"[{symbol}] Lỗi HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[{symbol}] Lỗi phân tích từ AI: {e}")
    
    return None

def main():
    if not os.path.exists(DATA_FILE):
        print("❌ Không tìm thấy file data.json!")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_db = json.load(f)

    # 1. Gom nhóm ngành và chọn ra Top 3 mã xuất sắc nhất mỗi nhóm ngành
    industry_groups = {}
    for symbol, data in stock_db.items():
        if data.get('close', 0) <= 0:
            continue
        sector = get_sector(symbol)
        if sector not in industry_groups:
            industry_groups[sector] = []
        industry_groups[sector].append((symbol, data))

    top_symbols_to_analyze = {} # Lưu kèm sector để truyền vào prompt
    for sector, items in industry_groups.items():
        items_sorted = sorted(items, key=lambda x: (x[1].get('total_score', 0), x[1].get('roe', 0)), reverse=True)
        top_3 = items_sorted[:3] # Lấy Top 3 đầu bảng mỗi ngành
        for sym, _ in top_3:
            top_symbols_to_analyze[sym] = sector
        print(f"📌 Nhóm ngành [{sector}] - Top 3 phân tích theo tiêu chí chuyên biệt: {[s[0] for s in top_3]}")

    print(f"\n🤖 Bắt đầu chạy phân tích theo tiêu chí riêng biệt cho từng nhóm ngành (Top 3 mỗi ngành)...")
    count = 0
    
    for symbol, data in stock_db.items():
        if data.get('close', 0) <= 0:
            continue
            
        # Chỉ gọi AI nếu mã nằm trong Top 3 của ngành
        if symbol in top_symbols_to_analyze:
            sector = top_symbols_to_analyze[symbol]
            updated_at = data.get("updated_at", "")
            ai_updated_at = data.get("ai_updated_at", "")
            
            if not data.get("ai_recommendation") or updated_at > ai_updated_at:
                print(f"🔍 [{sector}] Đang phân tích chuyên sâu mã: {symbol}...")
                ai_result = analyze_stock_with_ai(symbol, data, sector)
                
                if ai_result:
                    data["bctc"] = ai_result.get("bctc", "")
                    data["outlook"] = ai_result.get("outlook", "")
                    data["ai_recommendation"] = ai_result.get("recommendation", "")
                    data["ai_price_zone"] = ai_result.get("price_zone", "")
                    data["macro_view"] = ai_result.get("macro_view", "")
                    data["ai_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    count += 1
                    print(f"  -> ✅ Phân tích thành công cho {symbol}")
                else:
                    print(f"  -> ❌ Lỗi gọi AI cho {symbol}")
                
                time.sleep(1.5)
            else:
                print(f"💤 Bỏ qua {symbol} (Nhận định AI đã là mới nhất).")
        else:
            # Các mã ngoài Top 3 giữ nguyên vẹn dữ liệu cũ, không tốn token
            pass

    # Lưu lại file data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_db, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 Hoàn thành! Đã cập nhật phân tích theo tiêu chí đặc thù ngành cho {count} mã Top đầu.")

if __name__ == "__main__":
    main()
