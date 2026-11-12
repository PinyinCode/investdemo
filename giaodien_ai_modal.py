# -*- coding: utf-8 -*-
"""giaodien_ai_modal.py — Modal AI + Simulator DCA."""


def build_ai_modal_html():
    return r"""
    <!-- MODAL AI -->
    <div id="ai-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm hidden p-3 md:p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90dvh]">

            <!-- HEADER MODAL -->
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
                    <!-- NÚT CHẤM ĐIỂM LẠI (ĐÃ THÊM CLASS HIDDEN) -->
                    <button type="button" onclick="triggerRescore()" id="btn-modal-rescore" class="hidden px-2 py-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-bold transition" title="Chấm điểm lại mã này">
                        <i class="fa-solid fa-calculator"></i>
                    </button>
                    
                    <!-- NÚT PHÂN TÍCH AI (ĐÃ THÊM CLASS HIDDEN) -->
                    <button type="button" onclick="triggerAIAnalyze()" id="btn-modal-ai" class="hidden px-2 py-1.5 bg-fuchsia-600/20 hover:bg-fuchsia-600/40 text-fuchsia-400 border border-fuchsia-500/30 rounded-lg text-xs font-bold transition" title="Chạy AI phân tích lại mã này">
                        <i class="fa-solid fa-robot"></i>
                    </button>
                    
                    <div class="text-right">
                        <span id="modal-price" class="text-sm md:text-base font-black text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">--</span>
                        <p id="modal-sector" class="text-[9px] text-slate-400 mt-0.5 text-right">--</p>
                    </div>
                    <button type="button" onclick="closeModal()" class="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            </div>

            <!-- TABS -->
            <div class="flex border-b border-slate-800 bg-slate-900 px-5 pt-2 gap-3">
                <button type="button" onclick="switchAiTab('eval')" id="tab-btn-eval" class="px-4 py-2 text-xs font-bold text-emerald-400 border-b-2 border-emerald-500 transition">
                    <i class="fa-solid fa-robot mr-1.5"></i> Đánh Giá & Phân Tích AI
                </button>
                <button type="button" onclick="switchAiTab('simulator')" id="tab-btn-simulator" class="px-4 py-2 text-xs font-bold text-slate-400 hover:text-white transition">
                    <i class="fa-solid fa-calculator mr-1.5 text-emerald-400"></i> Giả Lập Tích Sản (DCA)
                </button>
            </div>

            <!-- BODY -->
            <div class="p-5 overflow-y-auto space-y-4 flex-grow">

                <!-- TÊN DOANH NGHIỆP + BADGE -->
                <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center text-xs">
                    <div>
                        <span class="text-[10px] text-slate-400 block uppercase font-semibold">Tên doanh nghiệp</span>
                        <span id="modal-company-name" class="font-bold text-white text-sm">--</span>
                    </div>
                    <div id="modal-cheap-badge-container"></div>
                </div>

                <!-- CHỈ SỐ CƠ BẢN -->
                <div class="grid grid-cols-4 md:grid-cols-8 gap-2 bg-slate-950/50 p-3 rounded-xl border border-slate-800 text-center">
                    <div><span class="text-[10px] text-slate-500 block">P/E</span><span id="modal-pe" class="text-sm font-bold text-slate-200">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">P/B</span><span id="modal-pb" class="text-sm font-bold text-slate-200">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">EPS</span><span id="modal-eps" class="text-sm font-bold text-slate-200">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">ROE</span><span id="modal-roe" class="text-sm font-bold text-blue-400">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">ROA</span><span id="modal-roa" class="text-sm font-bold text-indigo-400">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">Cổ tức</span><span id="modal-div" class="text-sm font-bold text-amber-400">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">SL Cổ phiếu</span><span id="modal-shares" class="text-sm font-bold text-emerald-400">--</span></div>
                    <div><span class="text-[10px] text-slate-500 block">Vốn hóa</span><span id="modal-mktcap" class="text-sm font-bold text-emerald-400">--</span></div>
                </div>

                <div id="modal-final-decision"></div>
                <div id="modal-fair-zone"></div>

                <!-- QUY TẮC VÀNG -->
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
                        <div class="pt-1 border-t border-slate-800 text-[10px] text-slate-500 italic">
                            Vùng mua chỉ là "giá". Quyết định cuối = Vùng mua + Chất lượng (PTCB) + Thời điểm (PTKT) + Định giá.
                        </div>
                    </div>
                </details>

                <!-- PRO METRICS -->
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

                <!-- TAB EVAL -->
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

                <!-- TAB SIMULATOR -->
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

            <!-- FOOTER -->
            <div class="bg-slate-950 px-5 py-3 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500">
                <div class="flex flex-col gap-0.5">
                    <span id="modal-time" class="text-indigo-400"><i class="fa-solid fa-robot mr-1"></i> AI phân tích lúc: --</span>
                    <span id="modal-price-time" class="text-emerald-500"><i class="fa-solid fa-clock mr-1"></i> Giá cập nhật lúc: --</span>
                </div>
                <button type="button" onclick="closeModal()" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition font-bold shadow">Đóng</button>
            </div>
        </div>
    </div>
    """
