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
        print("✅ Đã gửi báo cáo sáng Telegram!")
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def generate_morning_report():
    if not os.path.exists("screener_results.json"):
        send_telegram("⚠️ Không tìm thấy file screener_results.json!")
        return

    with open("screener_results.json", "r", encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        send_telegram("⚠️ File screener_results.json rỗng!")
        return

    # Top 5 mã điểm cao nhất
    top_5 = sorted(results, key=lambda x: x.get("total_score", 0), reverse=True)[:5]
    top_5_text = ""
    for i, r in enumerate(top_5):
        top_5_text += f"{i+1}. <b>{r['symbol']}</b> ({r['total_score']}đ) - {r['final_decision']} - Giá: {r['close_price']:,.0f}đ\n"

    # Top 5 mã trong vùng mua rẻ nhất
    cheap = [r for r in results if r.get("valuation_verdict") == "RẺ - TRONG VÙNG MUA"]
    cheap.sort(key=lambda x: x.get("discount_to_fair_pct", 0), reverse=True)
    cheap_5 = cheap[:5]
    cheap_text = ""
    for r in cheap_5:
        cheap_text += f"- <b>{r['symbol']}</b>: Giá {r['close_price']:,.0f}đ (CK {r['discount_to_fair_pct']:.1f}%)\n"
    if not cheap_text:
        cheap_text = "Không có mã nào trong vùng mua hiện tại.\n"

    today_str = datetime.now().strftime("%d/%m/%Y")
    report = f"""☀️ <b>CHÀO BUỔI SÁNG! BÁO CÁO THỊ TRƯỜNG {today_str}</b>

🔥 <b>TOP 5 MÃ ĐIỂM CAO NHẤT:</b>
{top_5_text}

💰 <b>TOP 5 MÃ ĐANG RẺ NHẤT (Chiết khấu cao):</b>
{cheap_text}

📈 <b>THỐNG KÊ RỔ VN100:</b>
- Trong vùng mua: <b>{len(cheap)} mã</b>
- Tín hiệu MUA MẠNH: <b>{sum(1 for r in results if 'MUA MẠNH' in r.get('final_decision', ''))} mã</b>
- Tín hiệu MUA TÍCH SẢN: <b>{sum(1 for r in results if 'MUA TÍCH SẢN' in r.get('final_decision', ''))} mã</b>
- Cảnh báo TRÁNH: <b>{sum(1 for r in results if 'TRÁNH' in r.get('final_decision', ''))} mã</b>

🔗 Xem chi tiết: https://dautuchungkhoan.ddns.net
"""
    send_telegram(report)

if __name__ == "__main__":
    generate_morning_report()
