# -*- coding: utf-8 -*-
"""giaodien_screener.py — Module screener.

Gồm:
    - build_screener_html() : header + bộ lọc (search, sector, ranking, shock) + container card
    - build_screener_js()   : renderCards() + search suggestion + shock badge + watchlist button + refresh single
"""


# ══════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════

def build_screener_html():
    return r"""
    <!-- HEADER -->
    <header class="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center gap-4">
            <div class="flex items-center space-x-3">
                <div class="bg-emerald-600 text-white p-2 rounded-lg shadow-lg shadow-emerald-500/30">
                    <i class="fa-solid fa-scale-balanced text-lg"></i>
                </div>
                <div>
                    <h1 class="text-base md:text-lg font-bold tracking-wide text-white">Pro Quant Screener</h1>
                    <p class="text-[10px] text-slate-400">Hệ thống chấm điểm đặc thù theo Nhóm ngành | <span class="text-emerald-400 font-semibold"><i class="fa-regular fa-clock mr-1"></i>Cập nhật giá: <span id="header-last-update">Đang tải...</span></span></p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button type="button" onclick="refreshPrices()" class="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 border border-emerald-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-lg shadow-emerald-600/20" title="Cập nhật toàn bộ giá realtime">
                    <i class="fa-solid fa-rotate" id="refresh-icon"></i> <span class="hidden md:inline">Làm mới giá</span>
                </button>
                <button type="button" id="btn-admin-panel" onclick="openAdminModal()" class="px-3 py-2 bg-amber-600/20 border border-amber-500/40 text-amber-300 rounded-lg text-xs font-semibold transition hidden items-center gap-1.5">
                    <i class="fa-solid fa-user-shield"></i> <span class="hidden md:inline">Admin</span>
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-2 md:px-4 py-4">

        <!-- BỘ LỌC -->
        <div class="bg-slate-900 p-2 md:p-3 rounded-xl border border-slate-800 shadow-sm mb-4 space-y-2">
            <div class="grid grid-cols-2 md:grid-cols-3 gap-1.5 md:gap-3">

                <!-- Ô TÌM KIẾM MÃ (CÓ GỢI Ý) -->
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

                <!-- NGÀNH -->
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

                <!-- RANKING -->
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

            <!-- CHECKBOX FILTER -->
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 pt-1 border-t border-slate-800/80 text-xs">
                <label class="flex items-center gap-2 cursor-pointer select-none text-amber-300 font-bold hover:text-amber-200 transition">
                    <input type="checkbox" id="watchlist-filter" onchange="renderCards()" class="w-4 h-4 rounded bg-slate-950 border-amber-500 text-amber-600 focus:ring-amber-500 focus:ring-offset-slate-900 cursor-pointer">
                    <span><i class="fa-solid fa-bookmark mr-1 text-amber-400"></i> Chỉ xem mã đang theo dõi <span id="watchlist-count-badge" class="hidden ml-1 bg-amber-500 text-black text-[9px] font-black px-1.5 py-0.5 rounded-full">0</span></span>
                </label>

                <label class="flex items-center gap-2 cursor-pointer select-none text-emerald-300 font-bold hover:text-emerald-200 transition ml-0 md:ml-4">
                    <input type="checkbox" id="shock-filter" onchange="renderCards()" class="w-4 h-4 rounded bg-slate-950 border-emerald-500 text-emerald-600 focus:ring-emerald-500 focus:ring-offset-slate-900 cursor-pointer">
                    <span><i class="fa-solid fa-bolt mr-1 text-emerald-400"></i> Chỉ xem mã đột biến (Dòng tiền lớn)</span>
                </label>

                <span id="active-filter-status" class="text-[10px] text-slate-400 hidden md:inline ml-auto">Hiển thị toàn bộ danh sách</span>
            </div>
        </div>

        <!-- CONTAINER CARD -->
        <div id="stock-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
            <div class="col-span-full text-center py-12 text-slate-500">
                <i class="fa-solid fa-spinner spinner text-2xl text-emerald-500 mb-3 block"></i>
                <p>Đang tải dữ liệu...</p>
            </div>
        </div>
    </main>
    """


# ══════════════════════════════════════════════════════════
# JS
# ══════════════════════════════════════════════════════════

def build_screener_js():
    return r"""
    // ══════════════════════════════════════════════════
    // SEARCH SUGGESTIONS
    // ══════════════════════════════════════════════════

    let currentSuggestions = [];

    function handleSearchInput(val) {
        const term = val.trim().toUpperCase();
        const suggestBox = document.getElementById('search-suggestions');

        if (!term) {
            suggestBox.classList.add('hidden');
            document.getElementById('sector-filter').value = "ALL";
            document.getElementById('ranking-filter').value = "FINAL_BUY_ONLY";
            document.getElementById('shock-filter').checked = false;
            renderCards();
            return;
        }

        currentSuggestions = screenerResults.filter(item =>
            item.symbol.includes(term) ||
            (item.company_name && item.company_name.toUpperCase().includes(term))
        ).slice(0, 8);

        if (currentSuggestions.length === 0) {
            suggestBox.innerHTML = `<div class="px-2 py-1.5 text-xs text-slate-500">Không tìm thấy mã.</div>`;
            suggestBox.classList.remove('hidden');
        } else {
            let html = '';
            currentSuggestions.forEach((item, idx) => {
                html += `<button type="button" onclick="selectSuggestion('${item.symbol}')" class="w-full text-left px-2 py-1.5 rounded-lg text-xs font-bold transition flex justify-between items-center hover:bg-slate-800 text-slate-300 ${idx === 0 ? 'bg-slate-800/50' : ''}">
                    <span>${item.symbol}</span>
                    <span class="text-[9px] text-slate-500 font-normal truncate max-w-[100px]">${item.company_name || ''}</span>
                </button>`;
            });
            suggestBox.innerHTML = html;
            suggestBox.classList.remove('hidden');
        }
    }

    function handleSearchKeyDown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            if (currentSuggestions.length > 0) {
                selectSuggestion(currentSuggestions[0].symbol);
            }
        }
    }

    function selectSuggestion(symbol) {
        document.getElementById('search-input').value = symbol;
        document.getElementById('search-suggestions').classList.add('hidden');

        const item = screenerResults.find(s => s.symbol === symbol);
        if (item) {
            const sectorSelect = document.getElementById('sector-filter');
            sectorSelect.value = item.sector || "ALL";
            const rankingSelect = document.getElementById('ranking-filter');
            if (rankingSelect.value === 'FINAL_BUY_ONLY' && !item.final_decision.includes("MUA")) {
                rankingSelect.value = 'FINAL_DECISION_SORT';
            }
        }
        renderCards();
    }

    // Đóng suggestions khi click ra ngoài
    window.addEventListener('click', (e) => {
        const searchBox = document.getElementById('search-input');
        const searchSuggest = document.getElementById('search-suggestions');
        if (searchBox && searchSuggest && !searchBox.contains(e.target) && !searchSuggest.contains(e.target)) {
            searchSuggest.classList.add('hidden');
        }
    });

    // ══════════════════════════════════════════════════
    // RENDER CARDS
    // ══════════════════════════════════════════════════

    function renderCards() {
        const container = document.getElementById('stock-container');
        if (!container) return;

        const searchTerm = document.getElementById('search-input').value.toUpperCase();
        const selectedSector = document.getElementById('sector-filter').value;
        const isWatchlistOnly = document.getElementById('watchlist-filter').checked;
        const isShockOnly = document.getElementById('shock-filter').checked;
        const rankingMode = document.getElementById('ranking-filter').value;

        // ---- Filter ----
        let filtered = screenerResults.filter(item => {
            const matchSearch = item.symbol.includes(searchTerm) ||
                (item.company_name && item.company_name.toUpperCase().includes(searchTerm));
            const matchSector = (selectedSector === "ALL") ? true : (item.sector === selectedSector);
            const matchWatchlist = !isWatchlistOnly || userWatchlist.has(item.symbol);

            const pct = item.price_change_percent || 0;
            const vol = item.volume_percent || 0;
            const isShock = ((pct >= 3.0) || (pct <= -3.0)) && (vol >= 120.0);
            const matchShock = !isShockOnly || isShock;

            return matchSearch && matchSector && matchWatchlist && matchShock;
        });

        // ---- Sort ----
        if (rankingMode === "FINAL_BUY_ONLY") {
            filtered = filtered.filter(i => (i.final_decision || "").includes("MUA"));
            const order = { "🎯 MUA MẠNH": 0, "✅ MUA TÍCH SẢN": 1 };
            filtered.sort((a, b) => (order[a.final_decision] ?? 9) - (order[b.final_decision] ?? 9) || b.total_score - a.total_score);
        } else if (rankingMode === "FINAL_AVOID_ONLY") {
            filtered = filtered.filter(i => (i.final_decision || "").includes("TRÁNH"));
            filtered.sort((a, b) => a.total_score - b.total_score);
        } else if (rankingMode === "FINAL_DECISION_SORT") {
            const order = {
                "🎯 MUA MẠNH": 0, "✅ MUA TÍCH SẢN": 1,
                "⏳ CHỜ XÁC NHẬN KỸ THUẬT": 2, "⏳ CHỜ ĐỊNH GIÁ TỐT HƠN": 3,
                "⚠️ CHỜ VỀ VÙNG MUA": 4, "👀 THEO DÕI": 5,
                "⚠️ CẢNH BÁO LỢI NHUẬN ẢO": 6, "❌ TRÁNH": 7,
            };
            filtered.sort((a, b) => (order[a.final_decision] ?? 9) - (order[b.final_decision] ?? 9) || b.total_score - a.total_score);
        } else if (rankingMode === "VALUATION_VERDICT") {
            const order = { "RẺ - TRONG VÙNG MUA": 0, "HỢP LÝ - CHỜ ĐIỀU CHỈNH": 1, "HƠI ĐẮT - KHÔNG MUA": 2, "ĐẮT - TRÁNH": 3, "KHÔNG ĐỦ DỮ LIỆU": 4 };
            filtered.sort((a, b) => {
                const va = order[a.valuation_verdict] ?? 5;
                const vb = order[b.valuation_verdict] ?? 5;
                if (va !== vb) return va - vb;
                return (b.discount_to_fair_pct || 0) - (a.discount_to_fair_pct || 0);
            });
        } else if (rankingMode === "FUNDAMENTAL" || rankingMode === "NONE") filtered.sort((a, b) => b.fundamental_score - a.fundamental_score);
        else if (rankingMode === "TECHNICAL") filtered.sort((a, b) => b.technical_score - a.technical_score);
        else if (rankingMode === "VALUATION_SCORE") filtered.sort((a, b) => (b.valuation_score || 0) - (a.valuation_score || 0));
        else if (rankingMode === "ALL_SCORE") filtered.sort((a, b) => b.total_score - a.total_score);
        else filtered.sort((a, b) => a.symbol.localeCompare(b.symbol));

        // ---- Empty ----
        if (filtered.length === 0) {
            container.innerHTML = `<div class="col-span-full text-center py-8 text-slate-500">Không tìm thấy mã nào phù hợp với bộ lọc.</div>`;
            return;
        }

        // ---- Render ----
        container.innerHTML = '';
        filtered.forEach((item, index) => {
            let statusColor = "text-slate-400 bg-slate-800";
            let borderColor = "border-slate-700";
            let cardGlow = "";
            let displayRec = item.technical_status || "Tích lũy";
            if (displayRec.includes("MUA") || displayRec.includes("BREAKOUT") || displayRec.includes("GOM")) {
                statusColor = "text-emerald-400 bg-emerald-500/10";
                borderColor = "border-emerald-500/30";
            } else if (displayRec.includes("CHỜ") || displayRec.includes("TÍCH LŨY") || displayRec.includes("CẠN CUNG")) {
                statusColor = "text-amber-400 bg-amber-500/10";
                borderColor = "border-amber-500/30";
            }

            const finalDec = item.final_decision || "";
            const finalColor = item.final_decision_color || "slate";
            const finalReason = item.final_decision_reason || "";
            const fdStyle = FINAL_DECISION_STYLE[finalColor] || FINAL_DECISION_STYLE.slate;

            if (finalColor === "emerald") { borderColor = "border-emerald-500/60"; cardGlow = "glow-cheap-zone"; }
            else if (finalColor === "rose") { borderColor = "border-rose-500/50"; }
            else if (finalColor === "amber") { borderColor = "border-amber-500/40"; }

            // Decision badge
            let decisionBadgeHtml = "";
            if (finalDec) {
                decisionBadgeHtml = `<div class="${fdStyle.bg} ${fdStyle.border} border rounded-lg px-2 py-1.5 mb-2 flex items-center gap-1.5" title="${finalReason}">
                    <i class="fa-solid ${fdStyle.icon} ${fdStyle.text} text-xs"></i>
                    <span class="${fdStyle.text} text-[11px] font-black">${finalDec}</span>
                </div>`;
            }

            // Verdict badge
            const verdict = item.valuation_verdict || "";
            let verdictBadgeHtml = "";
            if (verdict.includes("RẺ")) {
                verdictBadgeHtml = `<span class="bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1"><i class="fa-solid fa-crosshairs"></i> Trong vùng mua</span>`;
            } else if (verdict.includes("HỢP LÝ")) {
                verdictBadgeHtml = `<span class="bg-amber-500/15 text-amber-300 border border-amber-500/40 text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1"><i class="fa-solid fa-scale-balanced"></i> Giá hợp lý</span>`;
            } else if (verdict.includes("HƠI ĐẮT") || verdict.includes("ĐẮT")) {
                verdictBadgeHtml = `<span class="bg-rose-500/15 text-rose-300 border border-rose-500/40 text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1"><i class="fa-solid fa-hourglass-half"></i> Chờ giá tốt hơn</span>`;
            }

            // Top badge
            let topBadge = "";
            if (rankingMode !== "NONE") {
                if (index === 0) { topBadge = `<span class="absolute -top-3 -left-2 bg-yellow-500 text-black text-xs font-black px-2 py-1 rounded shadow">#1</span>`; cardGlow = "glow-top1"; }
                else if (index === 1) { topBadge = `<span class="absolute -top-3 -left-2 bg-slate-300 text-black text-xs font-black px-2 py-1 rounded shadow">#2</span>`; cardGlow = "glow-top2"; }
                else if (index === 2) { topBadge = `<span class="absolute -top-3 -left-2 bg-amber-700 text-white text-xs font-black px-2 py-1 rounded shadow">#3</span>`; cardGlow = "glow-top3"; }
                else { topBadge = `<span class="absolute -top-3 -left-2 bg-indigo-600 text-white text-xs font-black px-2 py-1 rounded shadow">#${index + 1}</span>`; }
            }

            // Cheap badge
            let cheapBadgeHtml = "";
            if (cheapSymbolsSet.has(item.symbol)) {
                cheapBadgeHtml = `<span class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1" title="Doanh nghiệp định giá rẻ"><i class="fa-solid fa-gem text-[8px]"></i> Định giá rẻ</span>`;
            }

            // Shock badge
            let shockBadgeHtml = "";
            const pctChange = item.price_change_percent || 0;
            const isPriceShock = (pctChange >= 3.0) || (pctChange <= -3.0);
            const isVolumeShock = (item.volume_percent || 0) >= 120.0;
            if (isPriceShock && isVolumeShock) {
                const isUp = pctChange > 0;
                const colorClass = isUp ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" : "bg-rose-500/20 text-rose-300 border-rose-500/40";
                const iconClass = isUp ? "fa-arrow-trend-up" : "fa-arrow-trend-down";
                shockBadgeHtml = `<span class="${colorClass} border text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1" title="Dòng tiền ${isUp ? 'MUA VÀO' : 'BÁN RÒNG'}">
                    <i class="fa-solid ${iconClass}"></i> Vol: ${Math.round(item.volume_percent)}%
                </span>`;
            }

            // Watchlist + refresh buttons
            const isWatched = userWatchlist.has(item.symbol);
            const watchBtnHtml = `<button type="button" data-watch-btn="${item.symbol}" onclick="toggleWatchlist('${item.symbol}', event)" 
                class="px-1.5 py-0.5 rounded-md ${isWatched ? 'bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300' : 'bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-400'} text-xs transition"
                title="${isWatched ? 'Đang theo dõi — click để bỏ' : 'Thêm vào danh mục theo dõi'}">
                <i class="fa-${isWatched ? 'solid' : 'regular'} fa-bookmark ${isWatched ? 'text-amber-400' : 'text-slate-400'}"></i>
            </button>`;

            const refreshBtnHtml = `<button type="button" data-refresh-single onclick="event.stopPropagation(); refreshSinglePrice('${item.symbol}', this)" 
                class="px-1.5 py-0.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-400 text-xs transition"
                title="Cập nhật giá realtime cho mã này">
                <i class="fa-solid fa-rotate"></i>
            </button>`;

            // Score grid
            let scoreHtml = "";
            if (rankingMode !== "NONE") {
                const isFundActive = rankingMode === "FUNDAMENTAL";
                const isTechActive = rankingMode === "TECHNICAL";
                const isAllActive  = rankingMode === "ALL_SCORE";
                const isValActive  = rankingMode === "VALUATION_VERDICT" || rankingMode === "VALUATION_SCORE";
                const clsBase = "flex flex-col items-center justify-center py-1 rounded-md border text-[9px] leading-tight";
                const clsFund = isFundActive ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-300" : "bg-slate-900/60 border-slate-800 text-slate-400";
                const clsTech = isTechActive ? "bg-indigo-500/20 border-indigo-500/50 text-indigo-300" : "bg-slate-900/60 border-slate-800 text-slate-400";
                const clsVal  = isValActive  ? "bg-amber-500/20 border-amber-500/50 text-amber-300"   : "bg-slate-900/60 border-slate-800 text-slate-400";
                const clsAll  = isAllActive  ? "bg-indigo-500/20 border-indigo-500/50 text-indigo-300" : "bg-slate-900/60 border-slate-800 text-slate-400";

                scoreHtml = `
                    <div class="mt-1 bg-slate-950/60 rounded-lg border border-slate-800 p-1.5">
                        <div class="grid grid-cols-4 gap-1">
                            <div class="${clsBase} ${clsFund}"><span class="font-semibold opacity-80">Cơ bản</span><span class="font-black text-[11px]">${item.fundamental_score ?? '—'}</span></div>
                            <div class="${clsBase} ${clsTech}"><span class="font-semibold opacity-80">Kỹ thuật</span><span class="font-black text-[11px]">${item.technical_score ?? '—'}</span></div>
                            <div class="${clsBase} ${clsVal}"><span class="font-semibold opacity-80">Định giá</span><span class="font-black text-[11px]">${item.valuation_score ?? item.value_score ?? '—'}</span></div>
                            <div class="${clsBase} ${clsAll}"><span class="font-semibold opacity-80">Tổng hợp</span><span class="font-black text-[11px] text-amber-300">${item.total_score ?? '—'}</span></div>
                        </div>
                    </div>
                `;
            }

            // Price change
            let priceChangeHtml = '';
            if (item.price_change_available) {
                const pct = item.price_change_percent || 0;
                const color = item.price_color === 'emerald' ? 'text-emerald-400' : (item.price_color === 'rose' ? 'text-rose-400' : 'text-slate-400');
                const arrow = item.price_arrow || '—';
                priceChangeHtml = `<span class="text-[11px] font-bold ${color} flex items-center gap-0.5 mt-0.5">${arrow} ${Math.abs(pct).toFixed(2)}%</span>`;
            } else {
                priceChangeHtml = `<span class="text-[11px] font-bold text-slate-500 mt-0.5">—</span>`;
            }

            // Card
            const card = document.createElement('div');
            card.className = `relative bg-slate-900 rounded-xl border ${borderColor} ${cardGlow} p-4 shadow-lg hover:bg-slate-800/80 transition w-full flex flex-col justify-between mt-2 cursor-pointer`;
            card.onclick = () => openChartModal(item.symbol);

            card.innerHTML = `
                ${topBadge}
                <div>
                    ${decisionBadgeHtml}
                    <div class="flex justify-between items-start mb-3">
                        <div class="flex flex-col min-w-0 pr-2">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-xl font-black text-white">${item.symbol}</span>
                                ${watchBtnHtml}
                                ${refreshBtnHtml}
                                <button type="button" onclick="event.stopPropagation(); openModal('${item.symbol}')" class="text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 px-2 py-1 rounded-md border border-indigo-500/20 text-xs transition flex items-center gap-1" title="Xem chi tiết">
                                    <i class="fa-solid fa-robot"></i> <span class="hidden sm:inline">Quant [AI]</span>
                                </button>
                                <span class="text-[10px] px-2 py-1 rounded font-bold ${statusColor}">${displayRec}</span>
                            </div>
                            <div class="flex flex-wrap items-center gap-2 mt-1 text-[10px] text-slate-400">
                                <span class="shrink-0"><i class="fa-solid fa-tag mr-1"></i>${SECTOR_NAMES[item.sector] || item.sector}</span>
                                ${item.company_name ? `<span class="text-slate-500 shrink-0">•</span> <span class="text-slate-300 font-medium truncate max-w-[150px]" title="${item.company_name}">${item.company_name}</span>` : ''}
                                <span class="shrink-0 text-slate-500 italic" title="Thời gian cập nhật của riêng mã này">
                                    <i class="fa-regular fa-clock mr-0.5"></i>${item.updated_at || 'Chưa rõ'}
                                </span>
                                ${shockBadgeHtml}
                            </div>
                        </div>
                        <div class="text-right flex flex-col items-end shrink-0 ml-2 gap-1">
                            <div class="flex flex-col items-end leading-tight">
                                <span class="block text-lg font-bold text-emerald-400">${formatPrice(item.close_price)}</span>
                                ${priceChangeHtml}
                            </div>
                            ${verdictBadgeHtml}
                            ${cheapBadgeHtml}
                        </div>
                    </div>

                    <div class="grid grid-cols-4 gap-2 mb-2 bg-slate-950/50 p-2 rounded-lg border border-slate-800/50 text-center">
                        <div><span class="block text-[10px] text-slate-500 mb-0.5">P/E</span><span class="text-xs font-semibold text-slate-200">${item.pe > 0 ? item.pe.toFixed(1) : '—'}</span></div>
                        <div class="border-l border-slate-800"><span class="block text-[10px] text-slate-500 mb-0.5">P/B</span><span class="text-xs font-semibold text-slate-200">${item.pb > 0 ? item.pb.toFixed(1) : '—'}</span></div>
                        <div class="border-l border-slate-800"><span class="block text-[10px] text-slate-500 mb-0.5">ROE</span><span class="text-xs font-semibold text-blue-400">${formatPercent(item.roe)}</span></div>
                        <div class="border-l border-slate-800"><span class="block text-[10px] text-slate-500 mb-0.5">Điểm</span><span class="text-xs font-semibold text-amber-400">${item.total_score}đ</span></div>
                    </div>

                    ${(item.fair_value_low > 0 && item.fair_value_high > 0) ? `
                    <div class="flex items-center justify-between text-[10px] bg-slate-950/40 px-2 py-1 rounded border border-slate-800/60 mb-1">
                        <span class="text-slate-400"><i class="fa-solid fa-crosshairs text-emerald-400 mr-1"></i>Mua ≤</span>
                        <span class="font-bold text-emerald-300">${formatPrice(item.fair_value_low)}</span>
                        <span class="text-slate-500">|</span>
                        <span class="text-slate-400">Fair</span>
                        <span class="font-bold text-indigo-300">${formatPrice(item.fair_value_high)}</span>
                    </div>` : ''}
                </div>
                ${scoreHtml}
            `;
            container.appendChild(card);
        });
    }
    """
