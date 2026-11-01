import os
import time
import requests
import re
import json

DATA_FILE = "data.json"
BCTC_DIR = "bctc_data"  # Thư mục chứa các file JSON BCTC đã cào ở bước trước

ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "").strip()
API_URL = "https://ws-8lcqaxwxdv0h9xzy.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"

def load_bctc_data(symbol):
    """
    Đọc dữ liệu BCTC đã cào sẵn từ thư mục bctc_data/{symbol}.json
    Tóm tắt ngắn gọn các số liệu quý gần nhất để đưa vào prompt cho AI đọc.
    """
    file_path = os.path.join(BCTC_DIR, f"{symbol}.json")
    if not os.path.exists(file_path):
        return "Không có dữ liệu BCTC chi tiết trong hệ thống."
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            bctc_raw = json.load(f)
            
        # Trích xuất gọn gàng để tránh quá tải token của LLM
        summary_info = []
        
        # Xử lý kết quả kinh doanh (income_statement)
        if 'income_statement' in bctc_raw:
            inc_data = bctc_raw['income_statement']
            if isinstance(inc_data, list) and len(inc_data) > 0:
                summary_info.append("--- KẾT QUẢ KINH DOANH (CÁC QUÝ GẦN NHẤT) ---")
                # Lấy tối đa 4 quý gần nhất
                for item in inc_data[:4]:
                    period = item.get('period', item.get('quarter', 'N/A'))
                    year = item.get('year', 'N/A')
                    rev = item.get('revenue', item.get('netRevenue', 0))
                    profit = item.get('profitAfterTax', item.get('netProfit', 0))
                    summary_info.append(f"Kỳ {period}/{year}: Doanh thu = {rev:,.0f}, Lợi nhuận sau thuế = {profit:,.0f}")

        # Xử lý bảng cân đối kế toán (balance_sheet)
        if 'balance_sheet' in bctc_raw:
            bal_data = bctc_raw['balance_sheet']
            if isinstance(bal_data, list) and len(bal_data) > 0:
                summary_info.append("--- CÂN ĐỐI KẾ TOÁN (QUÝ MỚI NHẤT) ---")
                latest = bal_data[0] # Kỳ mới nhất
                for k, v in list(latest.items())[:15]: # Lấy 15 chỉ tiêu đầu quan trọng
                    summary_info.append(f"{k}: {v}")

        return "\n".join(summary_info) if summary_info else "Dữ liệu BCTC trống hoặc không đúng định dạng."
    except Exception as e:
        return f"Lỗi đọc file BCTC: {e}"

def check_if_analysis_needed(stock_db):
    """
    Kiểm tra tự động xem mã nào cần AI phân tích lại.
    """
    for symbol, data in stock_db.items():
        if data.get('close', 0) <= 0:
            continue
            
        updated_at = data.get("updated_at", "")
        ai_updated_at = data.get("ai_updated_at", "")
        ai_recommendation = data.get("ai_recommendation", "")
        
        if not ai_recommendation or not ai_updated_at or updated_at > ai_updated_at:
            return True
            
    return False

def analyze_stock_with_ai(symbol, data):
    if not ALIBABA_API_KEY:
        print(f"❌ LỖI: Biến môi trường ALIBABA_API_KEY đang bị trống!")
        return None

    # Load dữ liệu BCTC thực tế của doanh nghiệp
    bctc_text = load_bctc_data(symbol)

    # Prompt chuyên sâu kết hợp đọc BCTC thực tế
    prompt = f"""
    Bạn là một Chuyên gia Phân tích Tài chính Cấp cao kiêm Quản lý Quỹ Đầu tư (Portfolio Manager) xuất sắc. 
    Hãy thực hiện một bản **đánh giá phân tích chiến lược chuyên sâu, bám sát bản chất kinh doanh cốt lõi VÀ ĐỌC KỸ SỐ LIỆU BÁO CÁO TÀI CHÍNH (BCTC)** của mã cổ phiếu: {symbol}.

    --- DỮ LIỆU BÁO CÁO TÀI CHÍNH THỰC TẾ TRÍCH XUẤT TỪ HỆ THỐNG ---
    {bctc_text}
    -----------------------------------------------------------------

    NGUYÊN TẮC BÓC TÁCH ĐỘNG LỰC TĂNG TRƯỞNG & ĐỌC BCTC:
    1. **Nếu là BẤT ĐỘNG SẢN / HẠ TẦNG / KHU CÔNG NGHIỆP:** 
       - Đọc kỹ khoản "Người mua trả tiền trước" / "Doanh thu chưa thực hiện", tiến độ dự án, nợ vay trái phiếu và lượng hàng tồn kho (dở dang).
    2. **Nếu là BÁN LẺ & TIÊU DÙNG:** 
       - Đọc kỹ biên lợi nhuận gộp, vòng quay hàng tồn kho và chi phí bán hàng/quản lý doanh nghiệp (SG&A).
    3. **Nếu là SẢN XUẤT / THÉP / HÓA CHẤT / VẬT LIỆU:** 
       - Đọc kỹ biến động giá vốn, quy mô hàng tồn kho (rủi ro trích lập dự phòng giá xuống), và đòn bẩy tài chính.
    4. **Nếu là NGÂN HÀNG & CHỨNG KHOÁN:** 
       - Ngân hàng xem xét NIM, nợ xấu (NPL), tỷ lệ bao phủ nợ xấu (LLR); Chứng khoán xem xét tỷ trọng tự doanh (FVTPL) và cho vay margin.
    5. **Nếu là ĐIỆN & NĂNG LƯỢNG / DẦU KHÍ:** 
       - Xem xét khấu hao tài sản cố định, dòng tiền hoạt động kinh doanh (CFO) có dương và đều đặn không.

    DỮ LIỆU THỊ TRƯỜNG & TÀI CHÍNH HIỆN TẠI:
    - Giá đóng cửa hiện tại: {data.get('close', 0)} VNĐ | Khối lượng: {data.get('volume', 0)}
    - Chỉ số định giá cơ bản: P/E = {data.get('pe', 0)} | P/B = {data.get('pb', 0)}
    - Khả năng sinh lời: EPS = {data.get('eps', 0)} VNĐ | ROE = {data.get('roe', 0)}% | ROA = {data.get('roa', 0)}%
    - Cổ tức: {data.get('dividend_yield', 0)}%
    - Trạng thái kỹ thuật/nến thô: {data.get('recommendation', 'Chưa xác định')} | Vùng giá thô: {data.get('price_zone', 'Chưa có')}

    YÊU CẦU TRẢ VỀ BẢN PHÂN TÍCH CHI TIẾT (Dạng JSON thuần túy, tuyệt đối không dùng định dạng markdown như ```json):
    1. "bctc": **Đọc sâu vào số liệu BCTC ở trên (Viết chi tiết từ 5-7 câu):** Phân tích trực tiếp các con số thực tế về cấu trúc vốn, sức khỏe dòng tiền kinh doanh (CFO), tỷ lệ nợ vay/vốn chủ sở hữu, và chất lượng lợi nhuận. Chỉ rõ doanh nghiệp đang gặp rủi ro tài chính hay có điểm sáng cốt lõi nào từ BCTC quý gần nhất.
    2. "outlook": Đánh giá triển vọng định giá và biên an toàn (Viết từ 4-6 câu): Phân tích mức giá hiện tại so với giá trị thực dựa trên động lực tài chính chính.
    3. "recommendation": Đưa ra khuyến nghị hành động sắc bén, chuẩn mực (Ngắn gọn từ 3-6 từ, ví dụ: "Tích sản dài hạn giá hấp dẫn", "Định giá quá cao - Chờ chiết khấu").
    4. "price_zone": Vạch rõ chiến lược hành động giá chi tiết: Vùng giá gom hợp lý, kèm theo mốc cắt lỗ hoặc điểm gia tăng tỷ trọng.
    5. "macro_view": Phân tích bức tranh vĩ mô toàn cầu & triển vọng ngành tương lai (Viết từ 5-7 câu): Đan xen hài hòa vĩ mô với năng lực chống chịu thực tế của doanh nghiệp qua BCTC.

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
            # Làm sạch chuỗi phản hồi JSON
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

    if not check_if_analysis_needed(stock_db):
        print("💤 Dữ liệu không thay đổi. Không cần gọi AI để tiết kiệm tài nguyên.")
        return

    print(f"🤖 Chuyên gia AI đang đọc BCTC thực tế và phân tích chuyên sâu...")
    count = 0
    
    for i, (symbol, data) in enumerate(stock_db.items()):
        if data.get('close', 0) <= 0:
            continue
            
        updated_at = data.get("updated_at", "")
        ai_updated_at = data.get("ai_updated_at", "")
        
        if not data.get("ai_recommendation") or updated_at > ai_updated_at:
            print(f"[{i+1}/{len(stock_db)}] Đang đọc BCTC & phân tích mã: {symbol}...")
            ai_result = analyze_stock_with_ai(symbol, data)
            
            if ai_result:
                data["bctc"] = ai_result.get("bctc", "")
                data["outlook"] = ai_result.get("outlook", "")
                data["ai_recommendation"] = ai_result.get("recommendation", "")
                data["ai_price_zone"] = ai_result.get("price_zone", "")
                data["macro_view"] = ai_result.get("macro_view", "")
                data["ai_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                count += 1
                print(f"  -> ✅ Phân tích BCTC thành công")
            else:
                print(f"  -> ❌ Lỗi gọi AI, bỏ qua mã này")
            
            time.sleep(1.5)
        else:
            print(f"[{i+1}/{len(stock_db)}] Bỏ qua {symbol} (Đã có nhận định AI mới nhất)")

    if count > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(stock_db, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 Hoàn thành! Đã cập nhật bản phân tích BCTC chi tiết cho {count} mã vào data.json.")
    else:
        print("\nℹ️ Không có dữ liệu mới cần chạy.")

if __name__ == "__main__":
    main()
