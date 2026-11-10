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
from simulator import run_complex_backtest_simulation

OUTPUT_HTML = "index.html"
LAST_UPDATE_FILE = "last_update.json"
CHEAP_STOCKS_FILE = "cheap_stocks.json"
AUTH_CONFIG_FILE = "auth_config.json"
PRICE_API_URL = "https://quant-price-api.onrender.com"

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

    # 1. Chạy simulator
    print("\n📊 [1/6] Chạy simulator backtest...")
    run_complex_backtest_simulation()
    print("     ✅ Đã tính xong lãi suất lịch sử cho các mã.")

    # 2. Đọc data
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

    # 3. Build CSS/HTML/JS
    print("\n🔧 [3/6] Build CSS/HTML/JS các module...")
    
    ui_css = build_ui_css()
    auth_css = build_auth_lite_css()
    full_css = "\n".join(["/* ===== UI BASE ===== */", ui_css, "/* ===== AUTH LITE ===== */", auth_css])
    
    # ĐẶT BUILD_AUTH_LITE_HTML Ở ĐẦU TIÊN ĐỂ LUÔN ƯU TIÊN VỀ MẶT DOM
    body_parts = [
        build_auth_lite_html(auth_config),
        build_admin_modal_html(),
        build_screener_html(),
        build_ai_modal_html(),
        build_chart_modal_html(),
        build_log_console_html(),
    ]
    full_body = "\n\n".join(body_parts)

    ui_js = build_ui_js()
    auth_js = build_auth_lite_js(auth_config)
    screener_js = build_screener_js()
    admin_js = build_admin_js()
    core_js = build_core_js(
        price_api_url=PRICE_API_URL,
        firebase_config=firebase_config,
        cheap_symbols=sorted(cheap_symbols_set),
        cheap_stocks_groups=cheap_stocks_groups,
    )

    # Làm sạch config để tránh lỗi authDomain
    firebase_config_clean = _json_blob(firebase_config)
    cheap_groups_clean = _json_blob(cheap_stocks_groups)
    cheap_symbols_clean = _json_blob(sorted(cheap_symbols_set))

    full_js = "\n\n".join([
        f"/* ══ CONFIG ══ */\n"
        f"const PRICE_API_URL = {json.dumps(PRICE_API_URL)};\n"
        f"const firebaseConfig = {firebase_config_clean};\n"
        f"const cheapStocksGroups = {cheap_groups_clean};\n"
        f"const cheapSymbolsSet = new Set({cheap_symbols_clean});\n"
        f"if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);\n"
        f"window.auth = firebase.auth();\n"
        f"window.db = firebase.firestore();\n"
        f"// 🔴 ÉP KHÓA CỨNG NGAY LẬP TỨC KHI VỪA TẢI TRANG ĐỂ CHỐNG LỘ NỘI DUNG\n"
        f"document.body.classList.add('auth-locked');",

        f"/* ══ UI BASE JS ══ */\n{ui_js}",
        f"/* ══ SCREENER JS ══ */\n{screener_js}",
        f"/* ══ ADMIN JS ══ */\n{admin_js}",
        f"/* ══ CORE JS ══ */\n{core_js}",
    ])

    # 4. Ghép HTML shell
    print("\n🏗️  [4/6] Ghép HTML shell...")
    html_output = build_html_shell(css=full_css, body=full_body, js=full_js)

    # 5. Chèn auth JS
    print("\n🔐 [5/6] Inject auth-lite JS...")
    html_output = html_output.replace("</body>", f"\n<!-- AUTH LITE JS -->\n{auth_js}\n</body>")

    # 6. Ghi file
    print("\n💾 [6/6] Ghi index.html...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"     ✅ index.html — {os.path.getsize(OUTPUT_HTML)/1024:.1f} KB")
    print("\n🎉 HOÀN TẤT\n")

if __name__ == "__main__":
    generate_html()
