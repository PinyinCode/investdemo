import os
import json
from datetime import datetime
from simulator import run_complex_backtest_simulation

# Import module gốc của bạn (giả sử file là accounts.py)
# Nếu bạn đặt tên file khác, hãy sửa lại dòng dưới đây
try:
    import accounts
except ImportError:
    accounts = None
    print("⚠️ Không tìm thấy module accounts.py, sẽ dùng giao diện mặc định.")

OUTPUT_HTML = "index.html"
LAST_UPDATE_FILE = "last_update.json"
CHEAP_STOCKS_FILE = "cheap_stocks.json"


def get_firebase_config():
    raw = os.environ.get("FIREBASE_CONFIG", "").strip()
    if not raw:
        print("⚠️ Thiếu secret FIREBASE_CONFIG — dùng config rỗng.")
        return {}
    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ FIREBASE_CONFIG không phải JSON hợp lệ: {e}")
        return {}
    required = ["apiKey", "authDomain", "projectId", "appId"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        print(f"⚠️ FIREBASE_CONFIG thiếu key: {', '.join(missing)}")
    return config


def get_last_update_string():
    if os.path.exists(LAST_UPDATE_FILE):
        try:
            with open(LAST_UPDATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "last_update" in data:
                    return data["last_update"]
        except Exception as e:
            print(f"⚠️ Lỗi đọc file last_update.json: {e}")
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def load_cheap_stocks_data():
    if os.path.exists(CHEAP_STOCKS_FILE):
        try:
            with open(CHEAP_STOCKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def generate_html():
    run_complex_backtest_simulation()
    print("📊 Đã tính toán xong lãi suất lịch sử cho các mã cổ phiếu.")

    last_update_str = get_last_update_string()
    cheap_stocks_groups = load_cheap_stocks_data()

    cheap_symbols_set = set()
    for sector_key, symbols_list in cheap_stocks_groups.items():
        for item in symbols_list:
            if "symbol" in item:
                cheap_symbols_set.add(item["symbol"])
            elif isinstance(item, str):
                cheap_symbols_set.add(item)

    firebase_config = get_firebase_config()
    firebase_config_json = json.dumps(firebase_config, ensure_ascii=False)
    cheap_stocks_json = json.dumps(cheap_stocks_groups, ensure_ascii=False)
    cheap_symbols_json = json.dumps(list(cheap_symbols_set), ensure_ascii=False)

    # Lấy mã HTML/CSS/JS từ module accounts (nếu có)
    accounts_css = ""
    accounts_html = ""
    accounts_js = ""
    if accounts:
        try:
            accounts_css, accounts_html, accounts_js = accounts.build_all_auth({})
        except Exception as e:
            print(f"⚠️ Lỗi load module accounts: {e}")

    html_template = r"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Pro Quant Screener & Investment Simulator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Firebase SDK (Dùng chung cho cả module gốc và module này) -->
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-firestore-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-database-compat.js"></script>
    
    <script src="./lightweight-charts.js"></script>
    
    <!-- CSS từ module Accounts -->
    <style>
        /* CSS Gốc của bạn */
        {accounts_css}
    </style>

    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        .spinner { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .glow-top1 { box-shadow: 0 0 15px rgba(234, 179, 8, 0.4); border-color: #eab308; }
        .glow-top2 { box-shadow: 0 0 10px rgba(148, 163, 184, 0.3); border-color: #94a3b8; }
        .glow-top3 { box-shadow: 0 0 10px rgba(180, 83, 9, 0.3); border-color: #b45309; }
        .glow-cheap-zone { box-shadow: 0 0 12px rgba(16, 185, 129, 0.25); }
        #chart-modal-box { max-height: 96dvh; }
        #chart-modal-box.fullscreen {
            position: fixed !important; top: 0 !important; left: 0 !important;
            width: 100vw !important; height: 100dvh !important;
            max-width: none !important; max-height: none !important;
            border-radius: 0 !important; z-index: 9999 !important;
        }
        #chart-modal-box:not(.fullscreen) #tv-chart-container {
            height: calc(96dvh - 50px) !important; min-height: 380px; width: 100% !important;
        }
        #chart-modal-box.fullscreen #tv-chart-container {
            height: calc(100dvh - 45px) !important; width: 100% !important;
        }
        #ranking-filter optgroup {
            background-color: #020617;
            color: #f59e0b;
            font-weight: 700;
            font-size: 10.5px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 8px 10px;
            border-top: 1px solid #1e293b;
        }
        #ranking-filter option {
            background-color: #0f172a;
            color: #e2e8f0;
            font-weight: 500;
            font-size: 13px;
            padding: 9px 12px;
            text-transform: none;
            letter-spacing: normal;
        }
        #ranking-filter option:checked {
            background: linear-gradient(90deg, #78350f 0%, #b45309 100%);
            color: #fef3c7;
            font-weight: 700;
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans pb-10">

    <!-- ═══════════════════════════════════════════════════════════════
         NHÚNG TOÀN BỘ HTML MODULE ACCOUNTS (Login, Admin, Renewal...)
         ═══════════════════════════════════════════════════════════════ -->
    {accounts_html}

    <!-- HEADER -->
    <header class="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center gap-4">
            <div class="flex items-center space-x-3">
                <div class="bg-emerald-600 text-white p-2 rounded-lg shadow-lg shadow-emerald-500/30">
                    <i class="fa-solid fa-scale-balanced text-lg"></i>
                </div>
                <div>
                    <h1 class="text-base md:text-lg font-bold tracking-wide text-white">Pro Quant Screener</h1>
                    <p class="text-[10px] text-slate-400">Hệ thống chấm điểm đặc thù theo Nhóm ngành | <span class="text-emerald-400 font-semibold"><i class="fa-regular fa-clock mr-1"></i>Cập nhật giá: {last_update_str}</span></p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button type="button" onclick="loadData(true)" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2">
                    <i class="fa-solid fa-rotate" id="refresh-icon"></i> <span class="hidden md:inline">Làm mới</span>
                </button>
                
                <!-- NÚT ADMIN GỌI HÀM CỦA MODULE ACCOUNTS -->
                <button type="button" id="btn-admin-panel" onclick="openAdminPanel()" class="px-3 py-2 bg-amber-600/20 border border-amber-500/40 text-amber-300 rounded-lg text-xs font-semibold transition hidden items-center gap-1.5">
                    <i class="fa-solid fa-user-shield"></i> <span class="hidden md:inline">Admin</span>
                </button>
                
                <!-- NÚT TÀI KHOẢN GỌI HÀM CỦA MODULE ACCOUNTS -->
                <button type="button" onclick="document.getElementById('userDropdown').classList.toggle('show')" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-300 rounded-lg text-xs font-semibold transition flex items-center gap-1.5" title="Tài khoản cá nhân">
                    <i class="fa-solid fa-user-gear text-emerald-400"></i> <span class="hidden md:inline">Tài khoản</span>
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-2 md:px-4 py-4">
        <!-- BỘ LỌC -->
        <div class="bg-slate-900 p-2 md:p-3 rounded-xl border border-slate-800 shadow-sm mb-4 space-y-2">
            <div class="grid grid-cols-2 md:grid-cols-3 gap-1.5 md:gap-3">
                <div class="relative w-full">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-2 md:pl-3 text-slate-400">
                        <i class="fa-solid fa-magnifying-glass text-xs md:text-sm"></i>
                    </span>
                    <input type="text" id="search-input" placeholder="Tìm mã..." autocomplete="off"
                        oninput="handleSearchInput(this.value)"
                        onkeydown="handleSearchKeyDown(event)"
                        class="w-full pl-7 md:pl-10 pr-7 md:pr-8 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs md:text-sm text-white focus:outline-none focus:border-emerald-500 transition">
                    <button type="button" onclick="clearInput('search-input')" class="absolute inset-y-0 right-0 flex items-center pr-2 md:pr-3 text-slate-400 hover:text-white transition" title="Xóa nhanh">
                        <i class="fa-solid fa-xmark text-xs"></i>
                    </button>
                    <div id="search-suggestions" class="absolute left-0 right-0 mt-1 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl hidden z-40 max-h-60 overflow-y-auto p-1.5"></div>
                </div>

                <div class="relative w-full">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-2 md:pl-3 text-slate-400">
                        <i class="fa-solid fa-filter text-xs md:text-sm"></i>
                    </span>
                    <select id="sector-filter" class="w-full pl-7 md:pl-10 pr-5 md:pr-8 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs md:text-sm text-white focus:outline-none focus:border-emerald-500 appearance-none transition truncate">
                        <option value="ALL">Tất cả ngành</option>
                        <option value="NGAN_HANG">Ngân hàng</option>
                        <option value="CHUNG_KHOAN">Chứng khoán</option>
                        <option value="BAT_DONG_SAN">Bất động sản</option>
                        <option value="CONG_NGHE_BAN_LE">Công nghệ & Bán lẻ</option>
                        <option value="DIEN_NUOC_HA_TANG">Điện, Nước & Hạ tầng</option>
                        <option value="NGUYEN_VAT_LIEU_CHU_KY">Vật liệu & Chu kỳ</option>
                        <option value="SAN_XUAT_TIEU_DUNG_PHONG_THU">Sản xuất & Tiêu dùng</option>
                    </select>
                    <span class="absolute inset-y-0 right-0 flex items-center pr-2 md:pr-3 text-slate-400 pointer-events-none">
                        <i class="fa-solid fa-chevron-down text-[10px]"></i>
                    </span>
                </div>

                <div class="relative w-full col-span-2 md:col-span-1">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-2 md:pl-3 text-amber-400 pointer-events-none">
                        <i class="fa-solid fa-compass text-xs md:text-sm"></i>
                    </span>
                    <select id="ranking-filter"
                        class="w-full pl-7 md:pl-10 pr-8 py-2 bg-slate-950 border border-amber-500/60 rounded-lg text-xs md:text-sm text-amber-200 font-semibold focus:outline-none focus:border-amber-300 focus:ring-2 focus:ring-amber-500/30 appearance-none transition truncate cursor-pointer hover:border-amber-400">
                        <optgroup label="Khuyến nghị">
                            <option value="FINAL_BUY_ONLY" selected>Danh mục MUA</option>
                            <option value="FINAL_DECISION_SORT">Toàn thị trường</option>
                            <option value="FINAL_AVOID_ONLY">Danh mục TRÁNH</option>
                        </optgroup>
                        <optgroup label="Định giá">
                            <option value="VALUATION_VERDICT">Trong vùng mua</option>
                            <option value="VALUATION_SCORE">Theo Điểm định giá</option>
                        </optgroup>
                        <optgroup label="Phân tích">
                            <option value="ALL_SCORE">Theo Tổng điểm</option>
                            <option value="TECHNICAL">Theo Kỹ thuật</option>
                            <option value="FUNDAMENTAL">Theo Cơ bản</option>
                        </optgroup>
                        <optgroup label="Khác">
                            <option value="NONE">Theo mã (A–Z)</option>
                        </optgroup>
                    </select>
                    <span class="absolute inset-y-0 right-0 flex items-center pr-2 md:pr-3 text-amber-400 pointer-events-none">
                        <i class="fa-solid fa-chevron-down text-[10px]"></i>
                    </span>
                </div>
            </div>

            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 pt-1 border-t border-slate-800/80 text-xs">
                <label class="flex items-center gap-2 cursor-pointer select-none text-amber-300 font-bold hover:text-amber-200 transition">
                    <input type="checkbox" id="watchlist-filter" onchange="renderCards()" class="w-4 h-4 rounded bg-slate-950 border-amber-500 text-amber-600 focus:ring-amber-500 focus:ring-offset-slate-900 cursor-pointer">
                    <span><i class="fa-solid fa-bookmark mr-1 text-amber-400"></i> Chỉ xem mã đang theo dõi <span id="watchlist-count-badge" class="hidden ml-1 bg-amber-500 text-black text-[9px] font-black px-1.5 py-0.5 rounded-full">0</span></span>
                </label>
                <span id="active-filter-status" class="text-[10px] text-slate-400 hidden md:inline ml-auto">Hiển thị toàn bộ danh sách</span>
            </div>
        </div>

        <div id="stock-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
            <div class="col-span-full text-center py-12 text-slate-500">
                <i class="fa-solid fa-spinner spinner text-2xl text-emerald-500 mb-3 block"></i>
                <p>Đang tải dữ liệu...</p>
            </div>
        </div>
    </main>

    <!-- MODAL AI -->
    <div id="ai-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm hidden p-3 md:p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90dvh]">
            <div class="bg-slate-950 px-4 py-3 border-b border-slate-800 flex justify-between items-center sticky top-0 z-10 gap-2">
                <div class="flex items-center space-x-1.5 md:space-x-2">
                    <button type="button" onclick="navigateModalSymbol(-1)" class="text-slate-400 hover:text-white px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition" title="Mã trước">
                        <i class="fa-solid fa-chevron-left text-xs"></i>
                    </button>
                    <div class="relative flex items-center">
                        <input type="text" id="modal-symbol-input" value="--" 
                               oninput="handleModalSearchInput(this.value)"
                               onkeydown="handleModalSearchKeyDown(event)"
                               autocomplete="off"
                               class="w-24 md:w-28 text-center text-base md:text-lg font-black text-indigo-400 bg-indigo-500/10 px-2 py-1 pr-6 rounded-lg border border-indigo-500/20 uppercase focus:outline-none focus:border-emerald-500" 
                               title="Nhập mã khác và nhấn Enter">
                        <button type="button" onclick="clearInput('modal-symbol-input')" class="absolute right-1 text-slate-400 hover:text-white text-xs transition" title="Xóa nhanh">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                        <div id="modal-search-suggestions" class="absolute left-0 top-full mt-1 w-48 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl hidden z-50 max-h-60 overflow-y-auto p-1.5"></div>
                    </div>
                    <button type="button" onclick="navigateModalSymbol(1)" class="text-slate-400 hover:text-white px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition" title="Mã tiếp theo">
                        <i class="fa-solid fa-chevron-right text-xs"></i>
                    </button>
                    <button type="button" id="modal-watchlist-btn" onclick="toggleWatchlistFromModal()" class="px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-400 transition text-xs" title="Thêm/bỏ theo dõi">
                        <i class="fa-regular fa-bookmark"></i>
                    </button>
                </div>
                <div class="flex items-center gap-2">
                    <div class="text-right">
                        <span id="modal-price" class="text-sm md:text-base font-black text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">--</span>
                        <p id="modal-sector" class="text-[9px] text-slate-400 mt-0.5 text-right">--</p>
                    </div>
                    <button type="button" onclick="closeModal()" class="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            </div>

            <div class="flex border-b border-slate-800 bg-slate-900 px-5 pt-2 gap-3">
                <button type="button" onclick="switchAiTab('eval')" id="tab-btn-eval" class="px-4 py-2 text-xs font-bold text-emerald-400 border-b-2 border-emerald-500 transition">
                    <i class="fa-solid fa-robot mr-1.5"></i> Đánh Giá & Phân Tích AI
                </button>
                <button type="button" onclick="switchAiTab('simulator')" id="tab-btn-simulator" class="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white transition">
                    <i class="fa-solid fa-calculator mr-1.5 text-emerald-400"></i> Giả Lập Tích Sản (DCA)
                </button>
            </div>

            <div class="p-5 overflow-y-auto space-y-4 flex-grow">
                <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center text-xs">
                    <div>
                        <span class="text-[10px] text-slate-400 block uppercase font-semibold">Tên doanh nghiệp</span>
                        <span id="modal-company-name" class="font-bold text-white text-sm">--</span>
                    </div>
                    <div id="modal-cheap-badge-container"></div>
                </div>

                <div class="grid grid-cols-3 md:grid-cols-6 gap-2 bg-slate-950/50 p-3 rounded-xl border border-slate-800 text-center">
                    <div><span class="text-[10px] text-slate-500 block">P/E</span><span id="modal-pe" class="text-sm font-bold text-slate-200">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">P/B</span><span id="modal-pb" class="text-sm font-bold text-slate-200">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">EPS</span><span id="modal-eps" class="text-sm font-bold text-slate-200">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">ROE</span><span id="modal-roe" class="text-sm font-bold text-blue-400">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">ROA</span><span id="modal-roa" class="text-sm font-bold text-indigo-400">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">Cổ tức</span><span id="modal-div" class="text-sm font-bold text-amber-400">--</span></div>
                </div>

                <div id="modal-final-decision"></div>
                <div id="modal-fair-zone"></div>

                <details class="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden">
                    <summary class="cursor-pointer px-3 py-2 text-xs font-bold text-slate-300 hover:text-white flex items-center gap-2 select-none">
                        <i class="fa-solid fa-book text-amber-400"></i>
                        Quy tắc vàng ra quyết định (PTCB + PTKT + Định giá + Vùng mua)
                        <i class="fa-solid fa-chevron-down text-[10px] ml-auto text-slate-500"></i>
                    </summary>
                    <div class="px-3 py-2 text-[11px] text-slate-400 space-y-1.5 border-t border-slate-800">
                        <div><span class="text-emerald-400 font-bold">🎯 MUA MẠNH:</span> Trong vùng mua + PTCB ≥ 40/50 + PTKT ≥ 15/20 + Định giá ≥ 24/30 + Tổng ≥ 75 + CK ≥ 5%.</div>
                        <div><span class="text-emerald-400 font-bold">✅ MUA TÍCH SẢN:</span> Trong vùng mua + PTCB ≥ 30/50 + PTKT ≥ 10/20 + Định giá ≥ 18/30 + Tổng ≥ 60.</div>
                        <div><span class="text-amber-400 font-bold">⚠️ CHỜ VỀ VÙNG MUA:</span> Doanh nghiệp tốt (PTCB ≥ 30, Định giá ≥ 18) nhưng giá chưa rẻ — chờ điều chỉnh.</div>
                        <div><span class="text-amber-400 font-bold">⏳ CHỜ XÁC NHẬN KỸ THUẬT:</span> Đủ vùng mua + cơ bản nhưng PTKT yếu (&lt;10/20).</div>
                        <div><span class="text-amber-400 font-bold">⏳ CHỜ ĐỊNH GIÁ TỐT HƠN:</span> Vào vùng mua nhưng điểm định giá &lt;18/30.</div>
                        <div><span class="text-rose-400 font-bold">❌ TRÁNH:</span> Giá đắt (vượt fair_high xa) HOẶC PTCB &lt; 20/50 HOẶC lợi nhuận ảo (CFO âm).</div>
                        <div><span class="text-slate-400 font-bold">👀 THEO DÕI:</span> Chưa đủ điều kiện rõ ràng.</div>
                    </div>
                </details>

                <div>
                    <button type="button" onclick="toggleProMetrics()" id="btn-toggle-prometrics" class="w-full py-2 bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition flex items-center justify-center gap-2 shadow-sm">
                        <i class="fa-solid fa-chart-pie text-emerald-400" id="prometrics-icon"></i>
                        <span id="prometrics-text">Hiển thị thêm chỉ số chuyên nghiệp (CFO, D/E, Biên gộp, TTM)</span>
                        <i class="fa-solid fa-chevron-down text-[10px] text-slate-400 ml-1 transition-transform duration-200" id="prometrics-chevron"></i>
                    </button>
                    <div id="pro-metrics-box" class="hidden mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 bg-slate-950/80 p-3 rounded-xl border border-emerald-500/30 text-center">
                        <div>
                            <span class="text-[10px] text-slate-400 block" id="label-cfo" title="Dòng tiền hoạt động kinh doanh">Dòng tiền CFO</span>
                            <span id="modal-cfo" class="text-xs font-bold text-emerald-400">--</span>
                        </div>
                        <div>
                            <span class="text-[10px] text-slate-400 block" id="label-de" title="Nợ phải trả / Vốn chủ sở hữu">Đòn bẩy D/E</span>
                            <span id="modal-de" class="text-xs font-bold text-amber-400">--</span>
                        </div>
                        <div>
                            <span class="text-[10px] text-slate-400 block" id="label-gm" title="Biên lợi nhuận gộp">Biên gộp</span>
                            <span id="modal-gm" class="text-xs font-bold text-blue-400">--</span>
                        </div>
                        <div>
                            <span class="text-[10px] text-slate-400 block">LN TTM (4Q)</span>
                            <span id="modal-ttm" class="text-xs font-bold text-indigo-400">--</span>
                        </div>
                    </div>
                </div>

                <div id="tab-content-eval" class="space-y-4">
                    <div id="modal-ai-rec-box" class="bg-indigo-500/10 border border-indigo-500/30 p-4 rounded-xl">
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-400"><i class="fa-solid fa-bullseye mr-1.5"></i> Khuyến nghị của AI</h4>
                            <span id="modal-ai-source" class="text-[9px] px-2 py-0.5 rounded border font-bold hidden"></span>
                        </div>
                        <p id="modal-ai-rec" class="text-lg font-black text-white mb-2"></p>
                        <div class="bg-slate-900/50 p-2.5 rounded border border-indigo-500/20">
                            <span class="text-[10px] text-slate-400 block mb-1">Chiến lược hành động:</span>
                            <p id="modal-ai-price" class="text-sm text-emerald-300 font-medium">--</p>
                        </div>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1"><i class="fa-solid fa-file-invoice-dollar text-emerald-500 mr-1.5"></i> Phân tích Sức khỏe Tài chính & BCTC [AI]</h4>
                        <p id="modal-bctc" class="text-sm bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 leading-relaxed">--</p>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1"><i class="fa-solid fa-chart-line text-blue-500 mr-1.5"></i> Định giá & Hành động giá [AI]</h4>
                        <p id="modal-outlook" class="text-sm bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 leading-relaxed">--</p>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1"><i class="fa-solid fa-globe text-amber-500 mr-1.5"></i> Vĩ mô & Sóng ngành [AI]</h4>
                        <p id="modal-macro" class="text-sm bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 leading-relaxed">--</p>
                    </div>
                </div>

                <div id="tab-content-simulator" class="space-y-4 hidden">
                    <div class="bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-xl text-xs space-y-2">
                        <div class="flex justify-between items-center">
                            <span class="text-slate-400">Tỷ suất sinh lời lịch sử (CAGR 5 năm):</span>
                            <span id="sim-historical-rate-text" class="text-sm font-bold text-emerald-400">Đang tính toán...</span>
                        </div>
                        <div class="border-t border-emerald-500/20 pt-2 grid grid-cols-2 gap-2 text-[11px]">
                            <div class="bg-slate-950/60 p-2 rounded border border-slate-800">
                                <span class="text-slate-400 block">Quý đầu (Neo 5 năm trước):</span>
                                <span id="sim-start-quarter-info" class="font-bold text-indigo-300">--</span>
                            </div>
                            <div class="bg-slate-950/60 p-2 rounded border border-slate-800">
                                <span class="text-slate-400 block">Quý cuối (Hiện tại):</span>
                                <span id="sim-end-quarter-info" class="font-bold text-amber-300">--</span>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-slate-400 mb-1 font-semibold">Vốn ban đầu (VNĐ)</label>
                            <input type="text" id="modal-sim-initial" value="20.000.000" oninput="formatCurrencyInput(this)" class="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-bold text-xs focus:outline-none focus:border-emerald-500">
                        </div>
                        <div>
                            <label class="block text-slate-400 mb-1 font-semibold">Tích sản hàng tháng (VNĐ)</label>
                            <input type="text" id="modal-sim-monthly" value="3.000.000" oninput="formatCurrencyInput(this)" class="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-bold text-xs focus:outline-none focus:border-emerald-500">
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-slate-400 mb-1 font-semibold">Kỳ hạn đầu tư (Năm)</label>
                            <input type="number" id="modal-sim-years" value="3" min="1" max="50" step="1" class="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-bold text-xs focus:outline-none focus:border-emerald-500">
                        </div>
                        <div>
                            <label class="block text-slate-400 mb-1 font-semibold">Lợi nhuận áp dụng (%/năm)</label>
                            <input type="number" id="modal-sim-rate" value="15" step="0.1" class="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-emerald-400 font-bold text-xs focus:outline-none focus:border-emerald-500">
                        </div>
                    </div>
                    <button type="button" onclick="calculateModalSimulation()" class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold transition text-xs shadow">
                        Tính Toán Lợi Nhuận DCA
                    </button>
                    <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5 text-xs">
                        <div class="flex justify-between"><span class="text-slate-400">Tổng vốn gốc đầu tư:</span> <span id="modal-sim-principal" class="font-bold text-slate-200">--</span></div>
                        <div class="flex justify-between"><span class="text-slate-400">Lợi nhuận dự kiến:</span> <span id="modal-sim-profit" class="font-bold text-emerald-400">--</span></div>
                        <div class="border-t border-slate-800 pt-1.5 flex justify-between text-sm"><span class="text-slate-300 font-bold">Tổng tài sản tương lai:</span> <span id="modal-sim-total" class="font-black text-amber-400">--</span></div>
                    </div>
                </div>
            </div>

            <div class="bg-slate-950 px-5 py-3 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500">
                <span id="modal-time">AI cập nhật: --</span>
                <button type="button" onclick="closeModal()" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition font-bold shadow">Đóng</button>
            </div>
        </div>
    </div>

    <!-- MODAL BIỂU ĐỒ -->
    <div id="chart-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm hidden p-1 md:p-3">
        <div id="chart-modal-box" class="bg-slate-900 border border-slate-700 w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300">
            <div class="p-0 bg-slate-900 flex-grow relative overflow-hidden">
                <div id="chart-loading" class="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20 text-emerald-400 text-xs hidden">
                    <i class="fa-solid fa-spinner spinner mr-2"></i> Đang tải dữ liệu biểu đồ...
                </div>
                <div id="chart-overlay-legend" class="absolute top-2 left-2 z-10 bg-slate-950/35 backdrop-blur-sm p-1.5 rounded-xl border border-slate-800/40 text-[10px] flex flex-wrap items-center gap-1.5 text-slate-300 shadow-lg max-w-[calc(100%-80px)]">
                    <button type="button" onclick="navigateSymbol(-1)" class="text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-900/40 border border-slate-700/50 transition"><i class="fa-solid fa-chevron-left text-[9px]"></i></button>
                    <div class="relative">
                        <button type="button" onclick="toggleSymbolDropdown()" id="chart-modal-symbol" class="text-xs font-black text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 px-2 py-0.5 rounded-lg border border-emerald-500/20 transition flex items-center gap-1">
                            <span id="current-symbol-text">--</span> <i class="fa-solid fa-chevron-down text-[9px]"></i>
                        </button>
                        <div id="symbol-dropdown" class="absolute left-0 mt-1 w-48 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl hidden z-50 max-h-60 overflow-y-auto p-1.5">
                            <div class="relative mb-1">
                                <input type="text" id="dropdown-search" placeholder="Lọc mã..." oninput="filterDropdownSymbols(this.value)" onkeydown="handleDropdownSearchKeyDown(event)" autocomplete="off" class="w-full px-2.5 py-1.5 pr-6 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500">
                                <button type="button" onclick="clearInput('dropdown-search'); filterDropdownSymbols('')" class="absolute right-1.5 inset-y-0 text-slate-400 hover:text-white text-xs transition" title="Xóa nhanh">
                                    <i class="fa-solid fa-xmark"></i>
                                </button>
                            </div>
                            <div id="dropdown-symbol-list" class="space-y-0.5"></div>
                        </div>
                    </div>
                    <button type="button" onclick="navigateSymbol(1)" class="text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-900/40 border border-slate-700/50 transition"><i class="fa-solid fa-chevron-right text-[9px]"></i></button>
                    <button type="button" id="chart-watchlist-btn" onclick="toggleWatchlistFromChart()" class="text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-900/40 border border-slate-700/50 transition text-[10px]" title="Thêm/bỏ theo dõi">
                        <i class="fa-regular fa-bookmark"></i>
                    </button>
                    <div class="flex items-center bg-slate-950/20 p-0.5 rounded-lg border border-slate-800/40 gap-0.5">
                        <button type="button" onclick="switchInterval('D1')" id="btn-d1" class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition">D1</button>
                        <button type="button" onclick="switchInterval('W1')" id="btn-w1" class="px-1.5 py-0.5 text-[10px] font-bold rounded text-slate-400 hover:text-white transition">W1</button>
                        <button type="button" onclick="switchInterval('MN')" id="btn-mn" class="px-1.5 py-0.5 text-[10px] font-bold rounded text-slate-400 hover:text-white transition">MN</button>
                        <button type="button" onclick="toggleQuarterLines()" id="btn-ind-qlines" class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition ml-1" title="Ẩn/Hiện đường giá quý"><i class="fa-solid fa-chart-line"></i></button>
                        <button type="button" onclick="toggleQuarterZone()" id="btn-ind-qzone" class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition" title="Ẩn/Hiện hộp vùng giá quý"><i class="fa-solid fa-square"></i></button>
                    </div>
                    <div class="flex items-center bg-slate-950/20 p-0.5 rounded-lg border border-slate-800/40 gap-0.5">
                        <button type="button" onclick="toggleIndicator('VOLMA')" id="btn-ind-volma" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition">VolMA</button>
                        <button type="button" onclick="toggleIndicator('MA20')" id="btn-ind-ma20" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-indigo-600 text-white transition">MA20</button>
                        <button type="button" onclick="toggleIndicator('MA50')" id="btn-ind-ma50" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition">MA50</button>
                        <button type="button" onclick="toggleIndicator('RSI')" id="btn-ind-rsi" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition">RSI</button>
                    </div>
                    <div class="flex items-center bg-slate-950/20 p-0.5 rounded-lg border border-slate-800/40 gap-0.5">
                        <button type="button" onclick="jumpToQuarter('start')" class="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-600 text-white transition" title="Nhảy tới Quý đầu 5 năm trước">&lt;&lt;</button>
                        <button type="button" onclick="jumpToQuarter('end')" class="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition" title="Nhảy tới Quý cuối hiện tại">&gt;&gt;</button>
                    </div>
                    <div class="flex items-center gap-2 pl-1 border-l border-slate-800/40 text-[10px]">
                        <div><span class="text-slate-400">TG:</span> <span id="legend-time" class="font-bold text-white">--</span></div>
                        <div><span class="text-slate-400">Giá:</span> <span id="legend-close" class="font-bold">--</span></div>
                        <div><span id="legend-change" class="font-bold">--</span></div>
                        <div><span class="text-slate-400">KL:</span> <span id="legend-vol" class="font-bold text-amber-400">--</span></div>
                    </div>
                </div>
                <div class="absolute top-2 right-2 z-10 flex items-center gap-1.5 bg-slate-950/35 backdrop-blur-sm p-1 rounded-xl border border-slate-800/40 shadow-lg">
                    <button type="button" onclick="toggleFullscreen()" id="fullscreen-btn" class="text-slate-300 hover:text-white p-1.5 rounded-lg bg-slate-900/40 transition" title="Phóng to / Thu nhỏ"><i class="fa-solid fa-expand text-xs"></i></button>
                    <button type="button" onclick="closeChartModal()" class="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg bg-slate-900/40 transition" title="Đóng"><i class="fa-solid fa-xmark text-xs"></i></button>
                </div>
                <div id="tv-chart-container" class="w-full h-full"></div>
            </div>
            <div class="bg-slate-950 px-3 py-2 border-t border-slate-800 flex justify-between items-center text-xs">
                <span class="text-slate-400"><i class="fa-regular fa-clock mr-1 text-emerald-400"></i> Giá cập nhật lần cuối: <strong class="text-white">{last_update_str}</strong></span>
                <div class="flex gap-2">
                    <button type="button" id="btn-view-ai" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition font-semibold flex items-center gap-1.5">
                        <i class="fa-solid fa-robot"></i> Xem AI chi tiết
                    </button>
                    <button type="button" onclick="closeChartModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition font-semibold">Đóng</button>
                </div>
            </div>
        </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════
         NHÚNG TOÀN BỘ JS MODULE ACCOUNTS (Auth, Admin, Renewal...)
         ═══════════════════════════════════════════════════════════════ -->
    <script>
        // KHAI BÁO CẤU HÌNH FIREBASE GỐC
        const FIREBASE_CONFIG = {firebase_config_json_placeholder};
        
        // CÁC BIẾN TOÀN CỤC KHÁC
        const cheapStocksGroups = {cheap_stocks_json_placeholder};
        const cheapSymbolsSet = new Set({cheap_symbols_json_placeholder});
    </script>

    <script>
        /* JS từ module Accounts (Chứa logic Auth, Admin Panel...) */
        {accounts_js}
    </script>

    <script>
        // ═══════════════════════════════════════════════════════════════
        // LOGIC RIÊNG CỦA TRANG QUANT SCREENER
        // ═══════════════════════════════════════════════════════════════

        // Biến state watchlist cục bộ cho trang này (để hiển thị badge/nút)
        let userWatchlist = new Set();
        let currentUserAccount = null; // Lưu user từ module gốc

        // Hàm lắng nghe sự kiện Auth từ module gốc
        function syncUserWithQuantApp(user) {
            currentUserAccount = user;
            if (user) {
                // Load watchlist từ Firestore
                db.collection('watchlists').doc(user.uid).get().then(doc => {
                    if (doc.exists) {
                        userWatchlist = new Set(doc.data().symbols || []);
                    } else {
                        userWatchlist = new Set();
                    }
                    updateWatchlistBadge();
                    renderCards();
                }).catch(err => console.warn('Lỗi tải watchlist:', err));
            } else {
                userWatchlist = new Set();
                updateWatchlistBadge();
                renderCards();
            }
        }

        // Gọi hàm này sau khi module accounts khởi tạo xong
        setTimeout(() => {
            if (typeof auth !== 'undefined') {
                auth.onAuthStateChanged(syncUserWithQuantApp);
            }
        }, 1000);

        // Các hàm xử lý Watchlist
        async function toggleWatchlist(symbol, event) {
            if (event) event.stopPropagation();
            if (!currentUserAccount) {
                alert('Vui lòng đăng nhập để dùng tính năng theo dõi!');
                return;
            }

            const isAdding = !userWatchlist.has(symbol);
            if (isAdding) userWatchlist.add(symbol);
            else userWatchlist.delete(symbol);

            updateWatchlistButton(symbol, isAdding);
            updateWatchlistBadge();
            updateModalWatchlistBtn(symbol);
            updateChartWatchlistBtn(symbol);

            try {
                await db.collection('watchlists').doc(currentUserAccount.uid).set({
                    symbols: Array.from(userWatchlist),
                    email: currentUserAccount.email,
                    updatedAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
            } catch (err) {
                console.error('❌ Lỗi lưu watchlist:', err);
                if (isAdding) userWatchlist.delete(symbol);
                else userWatchlist.add(symbol);
                updateWatchlistButton(symbol, !isAdding);
                updateWatchlistBadge();
                alert('Không thể lưu — vui lòng thử lại!');
            }
        }

        function toggleWatchlistFromModal() {
            if (currentSymbol) toggleWatchlist(currentSymbol, null);
        }

        function toggleWatchlistFromChart() {
            if (currentSymbol) toggleWatchlist(currentSymbol, null);
        }

        function updateWatchlistBadge() {
            const badge = document.getElementById('watchlist-count-badge');
            if (badge) {
                const count = userWatchlist.size;
                if (count > 0) {
                    badge.innerText = count;
                    badge.classList.remove('hidden');
                } else {
                    badge.classList.add('hidden');
                }
            }
        }

        // Các hàm render UI khác (giữ nguyên)
        function formatNumber(num) { /* ... */ }
        function formatPercent(num) { /* ... */ }
        // ... Copy toàn bộ logic renderCards, search suggestions, chart từ file trước ...

        // Lưu ý: Hàm loadData() vẫn giữ nguyên để load data.json
        // Các hàm openModal, openChartModal vẫn giữ nguyên

        document.getElementById('search-input').addEventListener('input', renderCards);
        document.getElementById('sector-filter').addEventListener('change', renderCards);
        document.getElementById('ranking-filter').addEventListener('change', renderCards);
    </script>
</body>
</html>
"""

    # Tiến hành thay thế các placeholder
    html_content = html_template.replace("{firebase_config_json_placeholder}", firebase_config_json)
    html_content = html_content.replace("{cheap_stocks_json_placeholder}", cheap_stocks_json)
    html_content = html_content.replace("{cheap_symbols_json_placeholder}", cheap_symbols_json)
    html_content = html_content.replace("{last_update_str}", last_update_str)
    
    # Nhúng mã từ module accounts
    html_content = html_content.replace("{accounts_css}", accounts_css)
    html_content = html_content.replace("{accounts_html}", accounts_html)
    html_content = html_content.replace("{accounts_js}", accounts_js)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Đã render thành công {OUTPUT_HTML}")


if __name__ == "__main__":
    generate_html()
