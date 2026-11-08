import os
import json
import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ LỖI: Thiếu cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"📡 Telegram HTTP Status: {res.status_code}")
        print(f"📡 Telegram Response: {res.text}")
        if res.status_code == 200 and res.json().get("ok"):
            print("✅ Telegram xác nhận ĐÃ GỬI thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối Telegram: {e}")

def generate_evening_report():
    print("🔄 Đang tạo báo cáo tối...")
    if not os.path.exists("screener_results.json"):
        send_telegram("⚠️ Không tìm thấy file screener_results.json!")
        return

    with open("screener_results.json", "r", encoding="utf-8") as f:
        results = json.load(f)
    if not results:
        send_telegram("⚠️ File screener_results.json rỗng!")
        return

    # 1. Tín hiệu MUA MẠNH
    buy_strong = [r for r in results if "MUA MẠNH" in r.get("final_decision", "")]
    strong_text = ""
    if buy_strong:
        for r in buy_strong:
            strong_text += f"🔹 <b>{r['symbol']}</b>: {r.get('close_price', 0):,.0f}đ | {r.get('total_score', 0)}đ\n"
    else:
        strong_text = "Không có mã nào.\n"

    # 2. Tín hiệu MUA TÍCH SẢN
    buy_dca = [r for r in results if "MUA TÍCH SẢN" in r.get("final_decision", "")]
    dca_text = ""
    if buy_dca:
        for r in buy_dca:
            dca_text += f"🔸 <b>{r['symbol']}</b>: {r.get('close_price', 0):,.0f}đ | {r.get('total_score', 0)}đ\n"
    else:
        dca_text = "Không có mã nào.\n"

    # 3. Ngành có nhiều mã MUA nhất
    sector_buy = {}
    for r in results:
        if "MUA" in r.get("final_decision", ""):
            sector = r.get("sector", "Khác")
            if sector not in sector_buy:
                sector_buy[sector] = []
            sector_buy[sector].append(r['symbol'])
    
    sorted_sectors = sorted(sector_buy.items(), key=lambda x: len(x[1]), reverse=True)[:3]
    sector_text = ""
    for sector, syms in sorted_sectors:
        sector_text += f"🔹 <b>{sector}</b> ({len(syms)} mã): {', '.join(syms)}\n"
    if not sector_text:
        sector_text = "Không có nhóm ngành nào phát tín hiệu MUA.\n"

    # 4. Mã biến động mạnh (Tăng/Giảm giá)
    top_gainers = sorted([r for r in results if r.get("price_change_percent", 0) > 0], key=lambda x: x.get("price_change_percent", 0), reverse=True)[:3]
    top_losers = sorted([r for r in results if r.get("price_change_percent", 0) < 0], key=lambda x: x.get("price_change_percent", 0))[:3]
    
    movers_text = ""
    for r in top_gainers:
        movers_text += f"🔺 <b>{r['symbol']}</b>: +{r.get('price_change_percent', 0):.1f}% ({r.get('close_price', 0):,.0f}đ)\n"
    for r in top_losers:
        movers_text += f"🔻 <b>{r['symbol']}</b>: {r.get('price_change_percent', 0):.1f}% ({r.get('close_price', 0):,.0f}đ)\n"
    if not movers_text:
        movers_text = "Không có dữ liệu.\n"

    # 5. Mã đột biến khối lượng
    top_volume = sorted(results, key=lambda x: x.get("volume_percent", 0), reverse=True)[:3]
    volume_text = ""
    for r in top_volume:
        volume_text += f"💥 <b>{r['symbol']}</b>: {r.get('volume_percent', 0):.0f}% so với TB ({r.get('close_price', 0):,.0f}đ)\n"
    if not volume_text or top_volume[0].get("volume_percent", 0) == 0:
        volume_text = "Không có dữ liệu.\n"

    # Thống kê nhanh
    in_buy_zone = sum(1 for r in results if r.get("valuation_verdict") == "RẺ - TRONG VÙNG MUA")
    avoid_count = sum(1 for r in results if "TRÁNH" in r.get("final_decision", ""))

    today_str = datetime.now().strftime("%d/%m/%Y")
    report = f"""🌙 <b>BÁO CÁO THỊ TRƯỜNG TỐI {today_str}</b>

🎯 <b>TÍN HIỆU MUA MẠNH ({len(buy_strong)} mã):</b>
{strong_text}
✅ <b>TÍN HIỆU MUA TÍCH SẢN ({len(buy_dca)} mã):</b>
{dca_text}
🏭 <b>NGÀNH CÓ TÍN HIỆU MUA NHIỀU NHẤT:</b>
{sector_text}
🚀 <b>BIẾN ĐỘNG MẠNH NHẤT TRONG PHIÊN:</b>
{movers_text}
💥 <b>ĐỘT BIẾN KHỐI LƯỢNG:</b>
{volume_text}

📊 <b>TỔNG KẾT PHIÊN HÔM NAY:</b>
- Số mã trong vùng mua (Rẻ): <b>{in_buy_zone} mã</b>
- Số mã cần TRÁNH: <b>{avoid_count} mã</b>

🔗 Xem chi tiết: https://dautuchungkhoan.ddns.net
"""
    send_telegram(report)

if __name__ == "__main__":
    generate_evening_report()
