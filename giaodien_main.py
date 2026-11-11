# -*- coding: utf-8 -*-
"""giaodien_main.py — Entry point duy nhất cho toàn bộ pipeline."""

import os
import sys
import traceback
from datetime import datetime

REQUIRED_FILES = [
    ("giaodien_generate.py",    "File assemble chính"),
    ("giaodien_auth.py",        "Module auth (login + Admin/User)"),
    ("giaodien_ui.py",          "CSS/JS base + HTML shell"),
    ("giaodien_screener.py",    "Header + bộ lọc + card"),
    ("giaodien_ai_modal.py",    "Modal AI + DCA simulator"),
    ("giaodien_chart_modal.py", "Modal biểu đồ"),
    ("giaodien_log_console.py", "Khung log nổi"),
    ("giaodien_core_js.py",     "Core JS logic"),
    ("giaodien_admin.py",       "Module giao diện Super Admin"), # THÊM DÒNG NÀY
    # Đã bỏ simulator.py khỏi danh sách bắt buộc vì chạy ở workflow khác
    ("lightweight-charts.js",   "Thư viện biểu đồ (JS)"),
]

def check_environment():
    print("=" * 60)
    print("🔍 KIỂM TRA MÔI TRƯỜNG")
    print("=" * 60)
    if sys.version_info < (3, 7):
        print(f"❌ Cần Python >= 3.7")
        return False
    print(f"✅ Python {sys.version.split()[0]}")

    missing = []
    for fname, desc in REQUIRED_FILES:
        if os.path.exists(fname):
            print(f"✅ {fname:<28} — {desc}")
        else:
            print(f"❌ {fname:<28} — {desc} (THIẾU)")
            missing.append(fname)

    if missing:
        print(f"\n❌ Thiếu {len(missing)} file bắt buộc.")
        return False
    return True

def run_pipeline():
    started_at = datetime.now()
    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU RENDER HTML")
    print("=" * 60)
    try:
        from giaodien_generate import generate_html
        generate_html()
        
        # Tính toán thời gian chạy
        elapsed = (datetime.now() - started_at).total_seconds()
        print(f"\n✅ HOÀN TẤT TRONG {elapsed:.2f} GIÂY")
    except Exception as e:
        print(f"\n❌ Lỗi render: {e}")
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)
    sys.exit(run_pipeline())
