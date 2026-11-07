import time
from vnstock import Company

symbol = "ACB"
print(f"Đang thử lấy dữ liệu cho {symbol}...")

try:
    comp = Company(symbol=symbol, source='VCI')
    df = comp.overview()
    if df is not None and not df.empty:
        print("✅ THÀNH CÔNG! IP của bạn đã được mở khóa.")
        print("Tên công ty:", df.iloc[0].get('organ_name'))
    else:
        print("⚠️ API trả về rỗng. Có thể vẫn đang bị khóa.")
except Exception as e:
    print(f"❌ VẪN BỊ KHÓA: {e}")