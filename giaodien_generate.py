# -*- coding: utf-8 -*-
"""giaodien_generate.py — File assemble chính.

Gom CSS/HTML/JS từ các module giaodien_* → xuất index.html hoàn chỉnh.

Cấu trúc project:
    giaodien_main.py           : entry point wrapper (check môi trường)
    giaodien_generate.py       : file này — assemble chính
    giaodien_auth.py           : module auth (login Google/Email + QR gia hạn)
    auth_config.json           : config bank + packages + trial_days
    simulator.py               : backtest simulator (CAGR lịch sử)

    giaodien_ui.py             : CSS/JS base + HTML_SHELL + helper format
    giaodien_screener.py       : header + bộ lọc + container card
    giaodien_ai_modal.py       : modal AI + simulator DCA
    giaodien_chart_modal.py    : modal biểu đồ lightweight-charts
    giaodien_log_console.py    : khung log nổi (refresh giá)
    giaodien_admin.py          : modal admin panel
    giaodien_core_js.py        : JS logic chính (loadData, renderCards, chart...)

Chạy: python giaodien_generate.py
Hoặc: python giaodien_main.py  (khuyến nghị — có check môi trường trước)
"""

import os
import json
from datetime import datetime

# ── Import module template (prefix giaodien_) ──────────────
from giaodien_ui import (
    build_ui_css,
    build_ui_js,
    build_html_shell,
    HTML_SHELL_TEMPLATE,
)
from giaodien_screener import (
    build_screener_html,
    build_screener_js,
)
from giaodien_ai_modal import (
    build_ai_modal_html,
)
from giaodien_chart_modal import (
    build_chart_modal_html,
)
from giaodien_log_console import (
    build_log_console_html,
)
from giaodien_admin import (
    build_admin_modal_html,
    build_admin_js,
)

# ── Import module auth (đã đổi tên) ────────────────────────
from giaodien_auth import (
    build_auth_lite_css,
    build_auth_lite_html,
    build_auth_lite_js,
)

# ── Import core JS ─────────────────────────────────────────
from giaodien_core_js import build_core_js

# ── Simulator ──────────────────────────────────────────────
from simulator import run_complex_backtest_simulation


# ── Config hằng số ─────────────────────────────────────────
OUTPUT_HTML = "index.html"
LAST_UPDATE_FILE = "last_update.json"
CHEAP_STOCKS_FILE = "cheap_stocks.json"
AUTH_CONFIG_FILE = "auth_config.json"

PRICE_API_URL = "https://quant-price-api.onrender.com"


# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

def get_firebase_config():
    """Đọc Firebase config từ env FIREBASE_CONFIG (JSON string)."""
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
    """Đọc auth_config.json (bank, packages, trial_days)."""
    if os.path.exists(AUTH_CONFIG_FILE):
        try:
            with open(AUTH_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Lỗi đọc auth_config.json: {e}")
    return {"trial_days": 7, "bank_config": {}, "packages": []}


def get_last_update_string():
    """Đọc last_update.json → str. Fallback = now."""
    if os.path.exists(LAST_UPDATE_FILE):
        try:
            with open(LAST_UPDATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "last_update" in data:
                    return data["last_update"]
        except Exception as e:
            print(f"⚠️  Lỗi đọc file last_update.json: {e}")
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def load_cheap_stocks_data():
    """Đọc cheap_stocks.json → dict. Fallback = {}."""
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


# ══════════════════════════════════════════════════════════
# MAIN ASSEMBLE
# ══════════════════════════════════════════════════════════

def generate_html():
    """Pipeline chính: chạy simulator → build tất cả module → ghi index.html."""

    print("=" * 60)
    print("🚀 GIAODIEN_GENERATE — ASSEMBLE PIPELINE")
    print("=" * 60)

    # ── 1. Chạy simulator (tính CAGR lịch sử) ─────────────
    print("\n📊 [1/6] Chạy simulator backtest...")
    run_complex_backtest_simulation()
    print("     ✅ Đã tính xong lãi suất lịch sử cho các mã.")

    # ── 2. Đọc data JSON ───────────────────────────────────
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

    print(f"     • Cheap stocks : {len(cheap_symbols_set)} mã")
    print(f"     • Firebase     : {'OK' if firebase_config else 'EMPTY'}")
    print(f"     • Auth packages: {len(auth_config.get('packages', []))} gói")
    print(f"     • Trial days   : {auth_config.get('trial_days', '?')} ngày")

    # ── 3. Build từng module ───────────────────────────────
    print("\n🔧 [3/6] Build CSS/HTML/JS các module...")

    # CSS
    ui_css = build_ui_css()
    auth_css = build_auth_lite_css()
    full_css = "\n".join([
        "/* ===== UI BASE ===== */",         ui_css,
        "/* ===== AUTH LITE ===== */",       auth_css,
    ])
    print(f"     • CSS : {len(full_css):>6,} chars")

    # HTML body (thứ tự quan trọng!)
    body_parts = [
        build_auth_lite_html(auth_config),  # overlay đăng nhập + modal gia hạn
        build_admin_modal_html(),           # modal admin
        build_screener_html(),              # header + bộ lọc + container card
        build_ai_modal_html(),              # modal AI + DCA simulator
        build_chart_modal_html(),           # modal biểu đồ
        build_log_console_html(),           # khung log nổi
    ]
    full_body = "\n\n".join(body_parts)
    print(f"     • BODY: {len(full_body):>6,} chars")

    # JS
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

    full_js = "\n\n".join([
        f"/* ══ CONFIG ══ */\n"
        f"const PRICE_API_URL = {json.dumps(PRICE_API_URL)};\n"
        f"const firebaseConfig = {_json_blob(firebase_config)};\n"
        f"const cheapStocksGroups = {_json_blob(cheap_stocks_groups)};\n"
        f"const cheapSymbolsSet = new Set({_json_blob(sorted(cheap_symbols_set))});\n"
        f"if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);\n"
        f"window.auth = firebase.auth();\n"
        f"window.db = firebase.firestore();",

        f"/* ══ UI BASE JS ══ */\n{ui_js}",
        f"/* ══ SCREENER JS ══ */\n{screener_js}",
        f"/* ══ ADMIN JS ══ */\n{admin_js}",
        f"/* ══ CORE JS ══ */\n{core_js}",
    ])
    print(f"     • JS  : {len(full_js):>6,} chars")

    # ── 4. Build HTML shell ────────────────────────────────
    print("\n🏗️  [4/6] Ghép HTML shell...")
    html_output = build_html_shell(
        css=full_css,
        body=full_body,
        js=full_js,
    )
    print(f"     • Total: {len(html_output):>6,} chars")

    # ── 5. Chèn auth_lite_js SAU core_js ───────────────────
    print("\n🔐 [5/6] Inject auth-lite JS (sau cùng)...")
    # auth_js phải chạy SAU core_js để window.onAuthReady đã được định nghĩa
    html_output = html_output.replace(
        "</body>",
        f"\n<!-- AUTH LITE JS (inject sau core) -->\n{auth_js}\n</body>",
    )
    print(f"     • Auth JS: {len(auth_js):>6,} chars")

    # ── 6. Ghi file ────────────────────────────────────────
    print("\n💾 [6/6] Ghi index.html...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_output)

    size_kb = os.path.getsize(OUTPUT_HTML) / 1024
    print(f"     ✅ index.html — {size_kb:.1f} KB")

    # ── Verify số thẻ script ──────────────────────────────
    _opens = html_output.count("<script")
    _closes = html_output.count("</script>")
    print(f"\n🔍 Check: <script>={_opens}  </script>={_closes}")
    if _opens != _closes:
        print(f"❌ Lệch {abs(_opens - _closes)} thẻ script!")
    else:
        print(f"✅ Số thẻ script khớp ({_opens})")

    print("\n" + "=" * 60)
    print("🎉 HOÀN TẤT")
    print("=" * 60)


if __name__ == "__main__":
    generate_html()
