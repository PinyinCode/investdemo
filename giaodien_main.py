# -*- coding: utf-8 -*-
"""giaodien_main.py — Entry point duy nhất cho toàn bộ pipeline.

Chạy:
    python giaodien_main.py

Yêu cầu các file cùng thư mục:
    ── BẮT BUỘC ────────────────────────────────────
    giaodien_generate.py       : file assemble chính
    giaodien_auth.py           : module auth (login + QR gia hạn)
    giaodien_ui.py             : CSS/JS base + HTML shell
    giaodien_screener.py       : header + bộ lọc + card
    giaodien_ai_modal.py       : modal AI + DCA
    giaodien_chart_modal.py    : modal biểu đồ
    giaodien_log_console.py    : khung log nổi
    giaodien_admin.py          : modal admin panel
    giaodien_core_js.py        : JS logic chính
    simulator.py               : backtest (CAGR lịch sử)
    lightweight-charts.js      : thư viện biểu đồ

    ── TÙY CHỌN ────────────────────────────────────
    auth_config.json           : config bank + packages (default 7 ngày)
    cheap_stocks.json          : danh sách mã định giá rẻ (default rỗng)
    screener_results.json      : kết quả screener (bắt buộc để app chạy)
    data.json                  : dữ liệu cơ bản (fallback)
    last_update.json           : thời gian cập nhật (fallback = now)
    history/*.json             : lịch sử giá cho biểu đồ

Biến môi trường:
    FIREBASE_CONFIG  : JSON string Firebase config
                       export FIREBASE_CONFIG='{"apiKey":"...","authDomain":"...","projectId":"...","appId":"..."}'
"""

import os
import sys
import json
import traceback
from datetime import datetime


# ══════════════════════════════════════════════════════════
# KIỂM TRA FILE
# ══════════════════════════════════════════════════════════

REQUIRED_FILES = [
    ("giaodien_generate.py",    "File assemble chính"),
    ("giaodien_auth.py",        "Module auth (login + QR gia hạn)"),
    ("giaodien_ui.py",          "CSS/JS base + HTML shell"),
    ("giaodien_screener.py",    "Header + bộ lọc + card"),
    ("giaodien_ai_modal.py",    "Modal AI + DCA simulator"),
    ("giaodien_chart_modal.py", "Modal biểu đồ"),
    ("giaodien_log_console.py", "Khung log nổi"),
    ("giaodien_admin.py",       "Modal admin panel"),
    ("giaodien_core_js.py",     "Core JS logic"),
    ("simulator.py",            "Backtest simulator"),
    ("lightweight-charts.js",   "Thư viện biểu đồ (JS)"),
]

OPTIONAL_FILES = [
    ("auth_config.json",     "Config bank + packages"),
    ("cheap_stocks.json",    "Danh sách mã định giá rẻ"),
    ("screener_results.json","Kết quả screener (app sẽ báo lỗi nếu thiếu)"),
    ("data.json",            "Dữ liệu cơ bản"),
    ("last_update.json",     "Thời gian cập nhật"),
]


def check_environment():
    print("=" * 60)
    print("🔍 KIỂM TRA MÔI TRƯỜNG")
    print("=" * 60)

    # 1. Python version
    if sys.version_info < (3, 7):
        print(f"❌ Cần Python >= 3.7 (hiện tại: {sys.version})")
        return False
    print(f"✅ Python {sys.version.split()[0]}")

    # 2. File bắt buộc
    missing = []
    for fname, desc in REQUIRED_FILES:
        if os.path.exists(fname):
            print(f"✅ {fname:<28} — {desc}")
        else:
            print(f"❌ {fname:<28} — {desc} (THIẾU)")
            missing.append(fname)

    if missing:
        print(f"\n❌ Thiếu {len(missing)} file bắt buộc: {', '.join(missing)}")
        print("   → Đảm bảo các file .py nằm cùng thư mục với giaodien_main.py")
        return False

    # 3. File tùy chọn
    print("\n📦 File tùy chọn:")
    for fname, desc in OPTIONAL_FILES:
        if os.path.exists(fname):
            print(f"   ✅ {fname:<28} — {desc}")
        else:
            print(f"   ⚠️  {fname:<28} — {desc}")

    # 4. FIREBASE_CONFIG
    print("\n🔐 Firebase config:")
    raw = os.environ.get("FIREBASE_CONFIG", "").strip()
    if not raw:
        print("   ⚠️  FIREBASE_CONFIG chưa set — app sẽ không đăng nhập được")
        print("   → Set: export FIREBASE_CONFIG='{\"apiKey\":\"...\",...}'")
    else:
        try:
            cfg = json.loads(raw)
            required_keys = ["apiKey", "authDomain", "projectId", "appId"]
            miss_keys = [k for k in required_keys if not cfg.get(k)]
            if miss_keys:
                print(f"   ⚠️  Thiếu key: {', '.join(miss_keys)}")
            else:
                print(f"   ✅ Hợp lệ (project: {cfg.get('projectId')})")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON lỗi: {e}")
            return False

    # 5. auth_config.json
    print("\n💳 Auth config:")
    if os.path.exists("auth_config.json"):
        try:
            with open("auth_config.json", "r", encoding="utf-8") as f:
                ac = json.load(f)
            trial = ac.get("trial_days", "?")
            pkgs = len(ac.get("packages", []))
            bank = ac.get("bank_config", {}).get("bank_name", "?")
            print(f"   ✅ Trial: {trial} ngày | {pkgs} gói | Bank: {bank}")
        except Exception as e:
            print(f"   ⚠️  Lỗi đọc auth_config.json: {e}")
    else:
        print("   ⚠️  Không có auth_config.json — dùng default")

    print("=" * 60)
    return True


# ══════════════════════════════════════════════════════════
# RUN PIPELINE
# ══════════════════════════════════════════════════════════

def run_pipeline():
    started_at = datetime.now()

    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU RENDER HTML")
    print("=" * 60)

    try:
        from giaodien_generate import generate_html

        print("⚙️  Đang chạy generate_html()...\n")
        generate_html()

        elapsed = (datetime.now() - started_at).total_seconds()

        print("\n" + "=" * 60)
        print(f"✅ HOÀN TẤT trong {elapsed:.2f}s")
        print("=" * 60)

        if os.path.exists("index.html"):
            size_kb = os.path.getsize("index.html") / 1024
            mtime = datetime.fromtimestamp(os.path.getmtime("index.html")).strftime("%d/%m/%Y %H:%M:%S")
            print(f"📄 Output  : index.html")
            print(f"   Size    : {size_kb:.1f} KB")
            print(f"   Updated : {mtime}")
            print(f"\n👉 Test local:")
            print(f"   python -m http.server 8000")
            print(f"   → mở http://localhost:8000/index.html")
        else:
            print("⚠️  Không tìm thấy index.html sau khi chạy!")
            return 1

        return 0

    except ImportError as e:
        print(f"\n❌ Lỗi import: {e}")
        print("   → Kiểm tra tên file trong thư mục có khớp với import không")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Lỗi render: {e}")
        traceback.print_exc()
        return 1


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "PRO QUANT SCREENER — RENDER PIPELINE" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")

    if not check_environment():
        print("\n❌ Môi trường chưa sẵn sàng — dừng.")
        sys.exit(1)

    if sys.stdin.isatty():
        print()
        ans = input("👉 Tiếp tục render? [Y/n]: ").strip().lower()
        if ans and ans not in ("y", "yes", "c", "có"):
            print("Đã hủy.")
            sys.exit(0)

    sys.exit(run_pipeline())


if __name__ == "__main__":
    main()
