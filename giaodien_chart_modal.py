# -*- coding: utf-8 -*-
"""giaodien_chart_modal.py — Modal biểu đồ lightweight-charts."""


def build_chart_modal_html():
    return r"""
    <!-- MODAL BIỂU ĐỒ -->
    <div id="chart-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm hidden p-1 md:p-3">
        <div id="chart-modal-box" class="bg-slate-900 border border-slate-700 w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300">
            <div class="p-0 bg-slate-900 flex-grow relative overflow-hidden">
                <div id="chart-loading" class="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20 text-emerald-400 text-xs hidden">
                    <i class="fa-solid fa-spinner spinner mr-2"></i> Đang tải dữ liệu biểu đồ...
                </div>

                <!-- LEGEND + TOOLBAR -->
                <div id="chart-overlay-legend" class="absolute top-2 left-2 z-10 bg-slate-950/35 backdrop-blur-sm p-1.5 rounded-xl border border-slate-800/40 text-[10px] flex flex-wrap items-center gap-1.5 text-slate-300 shadow-lg max-w-[calc(100%-80px)]">

                    <!-- NAVIGATE -->
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

                    <!-- WATCHLIST -->
                    <button type="button" id="chart-watchlist-btn" onclick="toggleWatchlistFromChart()" class="text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-900/40 border border-slate-700/50 transition text-[10px]" title="Thêm/bỏ theo dõi">
                        <i class="fa-regular fa-bookmark"></i>
                    </button>

                    <!-- INTERVAL -->
                    <div class="flex items-center bg-slate-950/20 p-0.5 rounded-lg border border-slate-800/40 gap-0.5">
                        <button type="button" onclick="switchInterval('D1')" id="btn-d1" class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition">D1</button>
                        <button type="button" onclick="switchInterval('W1')" id="btn-w1" class="px-1.5 py-0.5 text-[10px] font-bold rounded text-slate-400 hover:text-white transition">W1</button>
                        <button type="button" onclick="switchInterval('MN')" id="btn-mn" class="px-1.5 py-0.5 text-[10px] font-bold rounded text-slate-400 hover:text-white transition">MN</button>
                        <button type="button" onclick="toggleQuarterLines()" id="btn-ind-qlines" class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition ml-1" title="Ẩn/Hiện đường giá quý"><i class="fa-solid fa-chart-line"></i></button>
                        <button type="button" onclick="toggleQuarterZone()" id="btn-ind-qzone" class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition" title="Ẩn/Hiện hộp vùng giá quý"><i class="fa-solid fa-square"></i></button>
                    </div>

                    <!-- INDICATORS -->
                    <div class="flex items-center bg-slate-950/20 p-0.5 rounded-lg border border-slate-800/40 gap-0.5">
                        <button type="button" onclick="toggleIndicator('VOLMA')" id="btn-ind-volma" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition">VolMA</button>
                        <button type="button" onclick="toggleIndicator('MA20')" id="btn-ind-ma20" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-indigo-600 text-white transition">MA20</button>
                        <button type="button" onclick="toggleIndicator('MA50')" id="btn-ind-ma50" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition">MA50</button>
                        <button type="button" onclick="toggleIndicator('RSI')" id="btn-ind-rsi" class="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition">RSI</button>
                    </div>

                    <!-- JUMP QUARTER -->
                    <div class="flex items-center bg-slate-950/20 p-0.5 rounded-lg border border-slate-800/40 gap-0.5">
                        <button type="button" onclick="jumpToQuarter('start')" class="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-600 text-white transition" title="Nhảy tới Quý đầu 5 năm trước">&lt;&lt;</button>
                        <button type="button" onclick="jumpToQuarter('end')" class="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition" title="Nhảy tới Quý cuối hiện tại">&gt;&gt;</button>
                    </div>

                    <!-- LEGEND -->
                    <div class="flex items-center gap-2 pl-1 border-l border-slate-800/40 text-[10px]">
                        <div><span class="text-slate-400">TG:</span> <span id="legend-time" class="font-bold text-white">--</span></div>
                        <div><span class="text-slate-400">Giá:</span> <span id="legend-close" class="font-bold">--</span></div>
                        <div><span id="legend-change" class="font-bold">--</span></div>
                        <div><span class="text-slate-400">KL:</span> <span id="legend-vol" class="font-bold text-amber-400">--</span></div>
                    </div>
                </div>

                <!-- BUTTONS TOP RIGHT -->
                <div class="absolute top-2 right-2 z-10 flex items-center gap-1.5 bg-slate-950/35 backdrop-blur-sm p-1 rounded-xl border border-slate-800/40 shadow-lg">
                    <button type="button" onclick="toggleFullscreen()" id="fullscreen-btn" class="text-slate-300 hover:text-white p-1.5 rounded-lg bg-slate-900/40 transition" title="Phóng to / Thu nhỏ"><i class="fa-solid fa-expand text-xs"></i></button>
                    <button type="button" onclick="closeChartModal()" class="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg bg-slate-900/40 transition" title="Đóng"><i class="fa-solid fa-xmark text-xs"></i></button>
                </div>

                <!-- CHART CONTAINER -->
                <div id="tv-chart-container" class="w-full h-full"></div>
            </div>

            <!-- FOOTER -->
            <div class="bg-slate-950 px-3 py-2 border-t border-slate-800 flex justify-between items-center text-xs">
                <span class="text-slate-400"><i class="fa-regular fa-clock mr-1 text-emerald-400"></i> Giá cập nhật lần cuối: <strong class="text-white" id="chart-last-update">Đang tải...</strong></span>
                <div class="flex gap-2">
                    <button type="button" id="btn-view-ai" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition font-semibold flex items-center gap-1.5">
                        <i class="fa-solid fa-robot"></i> Xem AI chi tiết
                    </button>
                    <button type="button" onclick="closeChartModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition font-semibold">Đóng</button>
                </div>
            </div>
        </div>
    </div>
    """
