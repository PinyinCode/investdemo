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

# ══ IMPORT MODULE MỚI ══
from giaodien_admin_chat import build_admin_chat_css, build_admin_chat_html, build_admin_chat_js
from giaodien_chat_support import (
    build_chat_css, build_chat_html, build_chat_js, 
    build_quota_html, build_online_section_html, 
    build_quota_js, build_quota_init_js, build_telegram_notify_js
)

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

    print("\n📂 [1/6] Đọc data...")
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

    super_admins_raw = os.environ.get("SUPER_ADMINS", "")
    super_admins_list = [email.strip().lower() for email in super_admins_raw.split(",") if email.strip()]
    
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    print("\n🔧 [2/6] Build CSS/HTML/JS các module...")
    
    # 1. CSS (Chỉ lấy nội dung, không lấy thẻ <style>)
    # Sử dụng hàm replace để đề phòng các module cũ vẫn còn sót thẻ <style>
    def clean_css(css_str):
        return css_str.replace("<style>", "").replace("</style>", "").strip()

    ui_css = clean_css(build_ui_css())
    auth_css = clean_css(build_auth_lite_css())
    admin_chat_css = clean_css(build_admin_chat_css())
    chat_css = clean_css(build_chat_css())
    
    # Gộp tất cả CSS
    full_css = "\n".join([
        "/* ===== UI BASE ===== */", ui_css, 
        "/* ===== AUTH LITE ===== */", auth_css,
        "/* ===== ADMIN CHAT ===== */", admin_chat_css,
        "/* ===== CHAT SUPPORT ===== */", chat_css
    ])
    
    # 2. HTML
    auth_config["quota_html"] = build_quota_html()
    auth_config["online_html"] = build_online_section_html()

    body_parts = [
        build_auth_lite_html(auth_config),
        build_screener_html(),
        build_ai_modal_html(),
        build_chart_modal_html(),
        build_log_console_html(),
        build_admin_chat_html(),
        build_chat_html(),
    ]
    full_body = "\n\n".join(body_parts)

    # 3. JS
    ui_js = build_ui_js()
    auth_js = build_auth_lite_js(auth_config)
    screener_js = build_screener_js()
    admin_chat_js = build_admin_chat_js()
    chat_js = build_chat_js()
    quota_js = build_quota_js()
    quota_init_js = build_quota_init_js()
    tg_notify_js = build_telegram_notify_js()

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
        f"/* ══ ADMIN CHAT JS ══ */\n{admin_chat_js}",
        f"/* ══ CHAT SUPPORT JS ══ */\n{chat_js}",
        f"/* ══ QUOTA JS ══ */\n{quota_js}",
        f"/* ══ QUOTA INIT JS ══ */\n{quota_init_js}",
        f"/* ══ TELEGRAM NOTIFY JS ══ */\n{tg_notify_js}",
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
