# -*- coding: utf-8 -*-
"""giaodien_generate.py — File assemble chính."""

import os
import json
from datetime import datetime

from giaodien_ui import build_ui_css, build_ui_js, build_html_shell
from giaodien_screener import build_screener_html, build_screener_js
from giaodien_ai_modal import build_ai_modal_html
from giaodien_chart_modal import build_chart_modal_html
from giaodien_log_console import build_log_console_html

from giaodien_auth import build_auth_lite_css, build_auth_lite_html, build_auth_lite_js
from giaodien_core_js import build_core_js

OUTPUT_HTML = "index.html"
LAST_UPDATE_FILE = "last_update.json"
CHEAP_STOCKS_FILE = "cheap_stocks.json"
AUTH_CONFIG_FILE = "auth_config.json"
PRICE_API_URL = "https://quant-price-api.onrender.com"

# Số điện thoại Zalo Admin
ZALO_PHONE = "0528484668"

def get_firebase_config():
    raw = os.environ.get("FIREBASE_CONFIG", "").strip()
    if not raw:
        print("⚠️  Thiếu secret FIREBASE_CONFIG — dùng config rỗng.")
        return {}
    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ FIREBASE_CONFIG không phải JSON hợp lệ: {e}")
        return {}
    required = ["apiKey", "authDomain", "projectId", "appId"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        print(f"⚠️  FIREBASE_CONFIG thiếu key: {', '.join(missing)}")
    return config

def load_auth_config():
    if os.path.exists(AUTH_CONFIG_FILE):
        try:
            with open(AUTH_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Lỗi đọc auth_config.json: {e}")
    return {"trial_days": 7, "bank_config": {}, "packages": []}

def load_cheap_stocks_data():
    if os.path.exists(CHEAP_STOCKS_FILE):
        try:
            with open(CHEAP_STOCKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _json_blob(obj):
    """JSON compact, escape `</` để không phá </script>."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return s.replace("</", "<\\/")

def generate_html():
    print("=" * 60)
    print("🚀 GIAODIEN_GENERATE — ASSEMBLE PIPELINE")
    print("=" * 60)

    print("\n📊 [1/6] Bỏ qua simulator, sử dụng dữ liệu JSON có sẵn...")
    print("     ✅ Sẵn sàng đọc dữ liệu từ file.")

    print("\n📂 [2/6] Đọc data...")
    cheap_stocks_groups = load_cheap_stocks_data()
    cheap_symbols_set = set()
    for _sector_key, symbols_list in cheap_stocks_groups.items():
        for item in symbols_list:
            if isinstance(item, dict) and "symbol" in item:
                cheap_symbols_set.add(item["symbol"])
            elif isinstance(item, str):
                cheap_symbols_set.add(item)

    firebase_config = get_firebase_config()
    auth_config = load_auth_config()

    # Lấy danh sách Super Admin
    super_admins_raw = os.environ.get("SUPER_ADMINS", "")
    super_admins_list = [email.strip().lower() for email in super_admins_raw.split(",") if email.strip()]
    
    # Lấy cấu hình Telegram
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    
    print(f"     👑 Super Admins: {', '.join(super_admins_list) if super_admins_list else 'Chưa cấu hình'}")
    print(f"     🤖 Telegram: {'Đã cấu hình' if tg_token and tg_chat_id else 'Chưa cấu hình'}")

    print("\n🔧 [3/6] Build CSS/HTML/JS các module...")
    
    ui_css = build_ui_css()
    auth_css = build_auth_lite_css()
    full_css = "\n".join(["/* ===== UI BASE ===== */", ui_css, "/* ===== AUTH LITE ===== */", auth_css])
    
    # Tạo nút Zalo nổi & Hộp thông tin (FAB)
    zalo_button_html = f"""
    <!-- CSS CHO NÚT ZALO -->
    <style>
        .zalo-fab-wrapper {{
            position: fixed; right: 20px; bottom: 80px; z-index: 9999;
            display: flex; flex-direction: column; align-items: flex-end; gap: 12px;
            transition: left 0.3s ease, top 0.3s ease, right 0.3s ease, bottom 0.3s ease;
        }}
        
        .zalo-fab-btn {{
            width: 54px; height: 54px; border-radius: 50%;
            background: linear-gradient(135deg, #0068ff, #0052cc);
            color: #fff; display: flex; align-items: center; justify-content: center;
            font-size: 26px; cursor: grab; border: 3px solid #fff;
            box-shadow: 0 6px 20px rgba(0, 104, 255, 0.4);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            position: relative;
            animation: zaloShake 3s infinite ease-in-out;
            touch-action: none;
            user-select: none;
            -webkit-user-drag: none;
        }}
        
        .zalo-fab-btn:active {{
            cursor: grabbing;
            transform: scale(0.95) !important;
            animation: none;
        }}
        
        .zalo-fab-btn:hover {{
            transform: scale(1.1) !important;
            box-shadow: 0 10px 28px rgba(0, 104, 255, 0.6);
            animation: none;
        }}
        
        @keyframes zaloShake {{
            0%, 100% {{ transform: scale(1) rotate(0); }}
            5%, 15% {{ transform: scale(1.05) rotate(-10deg); }}
            10%, 20% {{ transform: scale(1.05) rotate(10deg); }}
            25% {{ transform: scale(1.02) rotate(-5deg); }}
            30% {{ transform: scale(1) rotate(0); }}
            50% {{ transform: scale(1.08) rotate(0); }}
            70% {{ transform: scale(1) rotate(0); }}
        }}

        .zalo-popup {{
            background: #fff; border-radius: 16px; padding: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15); border: 1px solid #e2e8f0;
            width: 260px; display: none; flex-direction: column; gap: 12px;
            transform-origin: bottom right; animation: popupIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        @keyframes popupIn {{
            from {{ opacity: 0; transform: scale(0.8) translateY(20px); }}
            to {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}
        .zalo-popup.show {{ display: flex; }}
        
        .zalo-popup-header {{ display: flex; align-items: center; gap: 12px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 12px; }}
        .zalo-avatar {{ width: 44px; height: 44px; border-radius: 50%; background: #0068ff; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; }}
        .zalo-info-title {{ font-size: 15px; font-weight: 800; color: #0f172a; margin-bottom: 2px; }}
        .zalo-info-sub {{ font-size: 13px; color: #64748b; }}
        
        .zalo-action-btn {{
            display: flex; align-items: center; justify-content: center; gap: 8px;
            background: linear-gradient(135deg, #0068ff, #0052cc); color: #fff;
            text-decoration: none; font-weight: 700; font-size: 14px;
            padding: 12px; border-radius: 12px; transition: all 0.2s;
        }}
        .zalo-action-btn:hover {{
            transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,104,255,0.3);
        }}
        
        @media (max-width: 768px) {{
            .zalo-fab-wrapper {{ bottom: 20px; right: 20px; }}
            .zalo-fab-btn {{ width: 48px; height: 48px; font-size: 22px; border-width: 2px; }}
            .zalo-popup {{ width: 240px; }}
        }}
    </style>

    <!-- HTML NÚT ZALO -->
    <div class="zalo-fab-wrapper" id="zaloFabWrapper">
        <div class="zalo-popup" id="zaloPopup">
            <div class="zalo-popup-header">
                <div class="zalo-avatar"><i class="fa-solid fa-headset"></i></div>
                <div>
                    <div class="zalo-info-title">Hỗ trợ Admin</div>
                    <div class="zalo-info-sub">SĐT: {ZALO_PHONE}</div>
                </div>
            </div>
            <a href="https://zalo.me/{ZALO_PHONE}" target="_blank" rel="noopener noreferrer" class="zalo-action-btn">
                <i class="fa-solid fa-paper-plane"></i> Nhắn tin qua Zalo
            </a>
        </div>
        
        <div class="zalo-fab-btn" id="zaloFabBtn" title="Liên hệ Admin">
            <i class="fa-solid fa-comment-dots"></i>
        </div>
    </div>

    <!-- SCRIPT XỬ LÝ KÉO THẢ VÀ BẤM -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var wrapper = document.getElementById('zaloFabWrapper');
            var zaloBtn = document.getElementById('zaloFabBtn');
            var zaloPopup = document.getElementById('zaloPopup');

            // --- HÀM RESET VỀ MẶC ĐỊNH (Góc dưới phải) ---
            function resetPosition() {{
                wrapper.style.left = 'auto';
                wrapper.style.top = 'auto';
                wrapper.style.right = '20px';
                // Trên mobile để bottom 20px, trên PC để 80px
                if (window.innerWidth <= 768) {{
                    wrapper.style.bottom = '20px';
                }} else {{
                    wrapper.style.bottom = '80px';
                }}
            }}

            // Gọi reset ngay khi vừa load trang
            resetPosition();

            // Tự động reset khi xoay màn hình điện thoại hoặc thay đổi kích thước cửa sổ
            window.addEventListener('resize', function() {{
                resetPosition();
            }});

            // --- LOGIC KÉO THẢ ---
            var isDragging = false;
            var hasMoved = false;
            var startX, startY, initialX, initialY;

            function dragStart(e) {{
                if (e.type === 'mousedown') {{
                    startX = e.clientX; startY = e.clientY;
                }} else if (e.type === 'touchstart') {{
                    startX = e.touches[0].clientX; startY = e.touches[0].clientY;
                }}
                
                var rect = wrapper.getBoundingClientRect();
                initialX = rect.left;
                initialY = rect.top;
                isDragging = true;
                hasMoved = false;
                
                // Khi bắt đầu kéo, chuyển from right/bottom sang left/top để dễ tính toán
                wrapper.style.right = 'auto';
                wrapper.style.bottom = 'auto';
                wrapper.style.left = initialX + 'px';
                wrapper.style.top = initialY + 'px';
                wrapper.style.transition = 'none';
                
                document.addEventListener('mousemove', dragMove);
                document.addEventListener('touchmove', dragMove, {{ passive: false }});
                document.addEventListener('mouseup', dragEnd);
                document.addEventListener('touchend', dragEnd);
            }}

            function dragMove(e) {{
                if (!isDragging) return;
                var currentX, currentY;
                
                if (e.type === 'mousemove') {{
                    currentX = e.clientX; currentY = e.clientY;
                }} else if (e.type === 'touchmove') {{
                    currentX = e.touches[0].clientX; currentY = e.touches[0].clientY;
                    if (e.cancelable) e.preventDefault(); // Ngăn cuộn trang
                }}

                var dx = currentX - startX;
                var dy = currentY - startY;

                if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {{
                    hasMoved = true;
                    zaloPopup.classList.remove('show'); // Ẩn popup nếu đang kéo
                }}

                if (hasMoved) {{
                    // Giới hạn không cho kéo ra ngoài màn hình
                    var newX = Math.max(0, Math.min(initialX + dx, window.innerWidth - wrapper.offsetWidth));
                    var newY = Math.max(0, Math.min(initialY + dy, window.innerHeight - wrapper.offsetHeight));
                    
                    wrapper.style.left = newX + 'px';
                    wrapper.style.top = newY + 'px';
                }}
            }}

            function dragEnd(e) {{
                if (!isDragging) return;
                isDragging = false;
                wrapper.style.transition = 'left 0.3s ease, top 0.3s ease, right 0.3s ease, bottom 0.3s ease';
                
                document.removeEventListener('mousemove', dragMove);
                document.removeEventListener('touchmove', dragMove);
                document.removeEventListener('mouseup', dragEnd);
                document.removeEventListener('touchend', dragEnd);

                if (hasMoved) {{
                    // Chặn sự kiện click giả sau khi kéo
                    zaloBtn.addEventListener('click', function(e) {{
                        e.stopPropagation(); e.preventDefault();
                    }}, {{ once: true, capture: true }});
                }}
            }}

            zaloBtn.addEventListener('mousedown', dragStart);
            zaloBtn.addEventListener('touchstart', dragStart, {{ passive: true }});

            // --- LOGIC BẤM MỞ POPUP ---
            zaloBtn.addEventListener('click', function(e) {{
                e.stopPropagation();
                if (!hasMoved) {{
                    zaloPopup.classList.toggle('show');
                }}
            }});

            document.addEventListener('click', function(e) {{
                if (zaloPopup.classList.contains('show') && !zaloPopup.contains(e.target) && e.target !== zaloBtn) {{
                    zaloPopup.classList.remove('show');
                }}
            }});
        }});
    </script>
    """

    body_parts = [
        build_auth_lite_html(auth_config),
        build_screener_html(),
        build_ai_modal_html(),
        build_chart_modal_html(),
        build_log_console_html(),
        zalo_button_html, # Chèn nút Zalo vào đây
    ]
    full_body = "\n\n".join(body_parts)

    ui_js = build_ui_js()
    auth_js = build_auth_lite_js(auth_config)
    screener_js = build_screener_js()
    
    core_js = build_core_js(
        price_api_url=PRICE_API_URL,
        firebase_config=firebase_config,
        cheap_symbols=sorted(cheap_symbols_set),
        cheap_stocks_groups=cheap_stocks_groups,
    )

    firebase_config_clean = _json_blob(firebase_config)
    cheap_groups_clean = _json_blob(cheap_stocks_groups)
    cheap_symbols_clean = _json_blob(sorted(cheap_symbols_set))
    super_admins_clean = _json_blob(super_admins_list)

    full_js = "\n\n".join([
        f"/* ══ CONFIG ══ */\n"
        f"const PRICE_API_URL = {json.dumps(PRICE_API_URL)};\n"
        f"const firebaseConfig = {firebase_config_clean};\n"
        f"const cheapStocksGroups = {cheap_groups_clean};\n"
        f"const cheapSymbolsSet = new Set({cheap_symbols_clean});\n"
        f"const SUPER_ADMINS = {super_admins_clean};\n" 
        f"const TELEGRAM_BOT_TOKEN = {json.dumps(tg_token)};\n"
        f"const TELEGRAM_CHAT_ID = {json.dumps(tg_chat_id)};\n"
        f"if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);\n"
        f"window.auth = firebase.auth();\n"
        f"window.db = firebase.firestore();",

        f"/* ══ UI BASE JS ══ */\n{ui_js}",
        f"/* ══ SCREENER JS ══ */\n{screener_js}",
        f"/* ══ CORE JS ══ */\n{core_js}",
    ])

    print("\n🏗️  [4/6] Ghép HTML shell...")
    html_output = build_html_shell(css=full_css, body=full_body, js=full_js)

    print("\n🔐 [5/6] Inject auth-lite JS...")
    html_output = html_output.replace("</body>", f"\n<!-- AUTH LITE JS -->\n{auth_js}\n</body>")

    print("\n💾 [6/6] Ghi index.html...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"     ✅ index.html — {os.path.getsize(OUTPUT_HTML)/1024:.1f} KB")
    print("\n🎉 HOÀN TẤT\n")

if __name__ == "__main__":
    generate_html()
