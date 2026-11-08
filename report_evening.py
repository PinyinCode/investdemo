import os
import json
import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Thiếu cấu hình Telegram!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
        print("✅ Đã gửi báo cáo tối Telegram!")
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def generate_evening_report():
    if not os.path.exists("screener_results.json"):
        send_telegram("⚠️ Không tìm thấy file screener_results.json!")
        return

    with open("screener_results.json", "r", encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        send_telegram("⚠️ File screener_results.json rỗng!")
        return

    # Top 3 mã tăng trưởng tốt nhất (dựa vào profit_growth_yoy)
    top_growth = sorted([r for r in results if r.get("profit_growth_yoy", 0) > 0], 
                        key=lambda x: x.get("profit_growth_yoy", 0), reverse=True)[:3]
    growth_text = ""
    for i, r in enumerate(top_growth):
        growth_text += f"{i+1}. <b>{r['symbol']}</b>: LN tăng {r['profit_growth_yoy']:.1f}% (Giá: {r['close_price']:,.0f}đ)\n"
    if not growth_text:
        growth_text = "Không có dữ liệu.\n"

    # Thống kê nhóm ngành có nhiều tín hiệu MUA
    sector_buy = {}
    for r in results:
        if "MUA" in r.get("final_decision", ""):
            sector = r.get("sector", "Khác")
            sector_buy[sector] = sector_buy.get(sector, 0) + 1
    top_sectors = sorted(sector_buy.items(), key=lambda x: x[1], reverse=True)[:3]
    sector_text = ""
    for sector, count in top_sectors:
        sector_text += f"- {sector}: {count} mã MUA\n"
    if not sector_text:
        sector_text = "Không có nhóm ngành nào phát tín hiệu MUA.\n"

    today_str = datetime.now().strftime("%d/%m/%Y")
    report = f"""🌙 <b>BÁO CÁO THỊ TRƯỜNG TỐI {today_str}</b>

📊 <b>TỔNG KẾT PHIÊN HÔM NAY:</b>
- Số mã trong vùng mua: <b>{sum(1 for r in results if r.get('valuation_verdict') == 'RẺ - TRONG VÙNG MUA')} mã</b>
- Số mã MUA MẠNH: <b>{sum(1 for r in results if 'MUA MẠNH' in r.get('final_decision', ''))} mã</b>
- Số mã MUA TÍCH SẢN: <b>{sum(1 for r in results if 'MUA TÍCH SẢN' in r.get('final_decision', ''))} mã</b>
- Số mã cần TRÁNH: <b>{sum(1 for r in results if 'TRÁNH' in r.get('final_decision', ''))} mã</b>

🚀 <b>TOP 3 MÃ TĂNG TRƯỞNG LỢI NHUẬN MẠNH NHẤT:</b>
{growth_text}

🏭 <b>NGÀNH CÓ TÍN HIỆU MUA NHIỀU NHẤT:</b>
{sector_text}

🔗 Xem chi tiết: https://dautuchungkhoan.ddns.net
"""
    send_telegram(report)

if __name__ == "__main__":
    generate_evening_report()
