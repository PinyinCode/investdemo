# -*- coding: utf-8 -*-
"""giaodien_core_js.py — Core JS logic chính."""

import json

def build_core_js(price_api_url, firebase_config, cheap_symbols, cheap_stocks_groups):
    firebase_json = json.dumps(firebase_config, ensure_ascii=False)
    cheap_symbols_json = json.dumps(cheap_symbols, ensure_ascii=False)
    cheap_groups_json = json.dumps(cheap_stocks_groups, ensure_ascii=False)

    return r"""
    // ══════════════════════════════════════════════════
    // STATE
    // ══════════════════════════════════════════════════
    let screenerResults = [];
    let symbolSimRates = {};
    let quarterlyMeanDetails = {};
    let currentSymbolHistory = null;
    let chartInstance = null;
    let candleSeriesInstance = null;
    let volumeSeriesInstance = null;
    let currentSymbol = null;
    let currentInterval = 'D1';
    let activeIndicators = { VOLMA: false, MA20: true, MA50: false, RSI: false, QLINES: true, QZONE: true };
    let currentActiveTab = 'eval';
    let userWatchlist = new Set();
    let currentUser = null;

    // ══════════════════════════════════════════════════
    // DICT STYLE
    // ══════════════════════════════════════════════════
    const SECTOR_NAMES = {
        "NGAN_HANG": "Ngân hàng", "CHUNG_KHOAN": "Chứng khoán", "BAT_DONG_SAN": "Bất động sản",
        "CONG_NGHE_BAN_LE": "Công nghệ & Bán lẻ", "DIEN_NUOC_HA_TANG": "Điện, Nước & Hạ tầng",
        "NGUYEN_VAT_LIEU_CHU_KY": "Vật liệu & Chu kỳ", "SAN_XUAT_TIEU_DUNG_PHONG_THU": "Sản xuất & Tiêu dùng",
        "KHAC": "Khác"
    };

    const FINAL_DECISION_STYLE = {
        "emerald": { bg: "bg-emerald-500/15", border: "border-emerald-500/50", text: "text-emerald-300", icon: "fa-circle-check" },
        "amber":   { bg: "bg-amber-500/15",   border: "border-amber-500/50",   text: "text-amber-300",   icon: "fa-hourglass-half" },
        "rose":    { bg: "bg-rose-500/15",    border: "border-rose-500/50",    text: "text-rose-300",    icon: "fa-triangle-exclamation" },
        "slate":   { bg: "bg-slate-700/40",   border: "border-slate-600/50",   text: "text-slate-300",   icon: "fa-eye" },
    };

    // ══════════════════════════════════════════════════
    // AUTH HOOKS
    // ══════════════════════════════════════════════════
    function parseDate(val) {
        if (!val) return null;
        if (typeof val.toDate === 'function') return val.toDate();
        const d = new Date(val);
        return isNaN(d.getTime()) ? null : d;
    }

    window.onAuthReady = async function(user) {
        currentUser = user;
        await loadUserWatchlist(user.uid);
        try {
            const doc = await window.db.collection('allowed_users').doc(user.email.toLowerCase()).get();
            if (doc.exists && doc.data().role === 'admin') {
                const adminBtn = document.getElementById('btn-admin-panel');
                if (adminBtn) { adminBtn.classList.remove('hidden'); adminBtn.classList.add('flex'); }
            }
        } catch (e) { console.warn('Không kiểm tra được role:', e); }
        if (typeof loadData === 'function') loadData(true);
    };

    window.onAuthLogout = function() {
        currentUser = null;
        userWatchlist = new Set();
    };

    // ══════════════════════════════════════════════════
    // WATCHLIST
    // ══════════════════════════════════════════════════
    async function loadUserWatchlist(uid) {
        try {
            const doc = await window.db.collection('watchlists').doc(uid).get();
            if (doc.exists) {
                const data = doc.data();
                userWatchlist = new Set(data.symbols || []);
            } else {
                userWatchlist = new Set();
            }
            updateWatchlistBadge();
        } catch (err) {
            console.warn('⚠️ Không tải được watchlist:', err);
            userWatchlist = new Set();
        }
    }

    async function toggleWatchlist(symbol, event) {
        if (event) event.stopPropagation();
        if (!currentUser) {
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
            await window.db.collection('watchlists').doc(currentUser.uid).set({
                symbols: Array.from(userWatchlist),
                email: currentUser.email,
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            }, { merge: true });
        } catch (err) {
            console.error('❌ Lỗi lưu watchlist:', err);
            if (isAdding) userWatchlist.delete(symbol);
            else userWatchlist.add(symbol);
            updateWatchlistButton(symbol, !isAdding);
            updateWatchlistBadge();
            updateModalWatchlistBtn(symbol);
            updateChartWatchlistBtn(symbol);
            alert('Không thể lưu — vui lòng thử lại!');
        }
    }

    function toggleWatchlistFromModal() { if (currentSymbol) toggleWatchlist(currentSymbol, null); }
    function toggleWatchlistFromChart() { if (currentSymbol) toggleWatchlist(currentSymbol, null); }

    function updateWatchlistButton(symbol, isWatched) {
        const btn = document.querySelector(`[data-watch-btn="${symbol}"]`);
        if (!btn) return;
        if (isWatched) {
            btn.innerHTML = '<i class="fa-solid fa-bookmark text-amber-400"></i>';
            btn.className = 'px-1.5 py-0.5 rounded-md bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-xs transition';
            btn.title = 'Đang theo dõi — click để bỏ';
        } else {
            btn.innerHTML = '<i class="fa-regular fa-bookmark text-slate-400"></i>';
            btn.className = 'px-1.5 py-0.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-400 text-xs transition';
            btn.title = 'Thêm vào danh mục theo dõi';
        }
    }

    function updateModalWatchlistBtn(symbol) {
        const btn = document.getElementById('modal-watchlist-btn');
        if (!btn) return;
        if (userWatchlist.has(symbol)) {
            btn.innerHTML = '<i class="fa-solid fa-bookmark text-amber-400"></i>';
            btn.className = 'px-2 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 transition text-xs';
        } else {
            btn.innerHTML = '<i class="fa-regular fa-bookmark text-slate-400"></i>';
            btn.className = 'px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-400 transition text-xs';
        }
    }

    function updateChartWatchlistBtn(symbol) {
        const btn = document.getElementById('chart-watchlist-btn');
        if (!btn) return;
        if (userWatchlist.has(symbol)) {
            btn.innerHTML = '<i class="fa-solid fa-bookmark text-amber-400"></i>';
            btn.className = 'text-amber-400 bg-amber-500/20 hover:bg-amber-500/30 px-1.5 py-0.5 rounded border border-amber-500/40 transition text-[10px]';
        } else {
            btn.innerHTML = '<i class="fa-regular fa-bookmark text-slate-400"></i>';
            btn.className = 'text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-900/40 border border-slate-700/50 transition text-[10px]';
        }
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

    // ══════════════════════════════════════════════════
    // LOAD DATA
    // ══════════════════════════════════════════════════
    async function loadData(showSpinner = false) {
        const icon = document.getElementById('refresh-icon');
        if (showSpinner && icon) icon.classList.add('spinner');
        try {
            const [screenerRes, ratesRes, detailsRes] = await Promise.all([
                fetch('screener_results.json?t=' + new Date().getTime()),
                fetch('symbol_sim_rates.json?t=' + new Date().getTime()).catch(() => ({ ok: false })),
                fetch('quarterly_mean_details.json?t=' + new Date().getTime()).catch(() => ({ ok: false }))
            ]);
            if (!screenerRes.ok) throw new Error('Không thể tải screener_results.json');
            let screenerData = await screenerRes.json();
            if (ratesRes.ok) symbolSimRates = await ratesRes.json();
            if (detailsRes.ok) quarterlyMeanDetails = await detailsRes.json();

            try {
                const timeRes = await fetch(`${PRICE_API_URL}/api/last-update?t=` + new Date().getTime());
                if (timeRes.ok) {
                    const timeData = await timeRes.json();
                    if (timeData.last_update && timeData.last_update !== "Chưa có dữ liệu") {
                        document.getElementById('header-last-update').innerText = timeData.last_update;
                    }
                }
            } catch (e) { console.warn("Không lấy được giờ cập nhật:", e); }

            let rawStockData = {};
            try {
                const dataRes = await fetch('data.json?t=' + new Date().getTime());
                if (dataRes.ok) rawStockData = await dataRes.json();
            } catch (e) {}

            let mongoPrices = {};
            try {
                const mongoRes = await fetch(`${PRICE_API_URL}/api/data?t=` + new Date().getTime());
                if (mongoRes.ok) {
                    const mongoJson = await mongoRes.json();
                    mongoPrices = mongoJson.data || {};
                }
            } catch (e) { console.warn("Không lấy được giá từ MongoDB:", e); }

            screenerResults = screenerData.map(item => {
                const sym = item.symbol;
                const extraData = rawStockData[sym] || {};
                const liveData = mongoPrices[sym] || {};
                let finalClosePrice = item.close_price || 0;
                if (liveData.close_price !== undefined) finalClosePrice = liveData.close_price;
                else if (liveData.close !== undefined) finalClosePrice = liveData.close;
                else if (extraData.close !== undefined) finalClosePrice = extraData.close;

                return {
                    ...item,
                    company_name: extraData.company_name !== undefined ? extraData.company_name : (item.company_name || extraData.organ_name || item.organ_name || ""),
                    market_cap: extraData.market_cap !== undefined ? extraData.market_cap : (item.market_cap || 0),
                    total_shares: extraData.total_shares !== undefined ? extraData.total_shares : (item.total_shares || 0),
                    eps: extraData.eps !== undefined ? extraData.eps : item.eps,
                    dividend_yield: extraData.dividend_yield !== undefined ? extraData.dividend_yield : item.dividend_yield,
                    pe: extraData.pe !== undefined ? extraData.pe : item.pe,
                    pb: extraData.pb !== undefined ? extraData.pb : item.pb,
                    roe: extraData.roe !== undefined ? extraData.roe : item.roe,
                    roa: extraData.roa !== undefined ? extraData.roa : item.roa,
                    cfo_latest: extraData.cfo_latest !== undefined ? extraData.cfo_latest : (item.cfo_latest || 0),
                    debt_to_equity: extraData.debt_to_equity !== undefined ? extraData.debt_to_equity : (item.debt_to_equity || 0),
                    gross_margin: extraData.gross_margin !== undefined ? extraData.gross_margin : (item.gross_margin || 0),
                    net_profit_ttm: extraData.net_profit_ttm !== undefined ? extraData.net_profit_ttm : (item.net_profit_ttm || 0),
                    close_price: finalClosePrice,
                    updated_at: liveData.updated_at || extraData.updated_at || "Chưa rõ",
                    open: liveData.open !== undefined ? liveData.open : null,
                    high: liveData.high !== undefined ? liveData.high : null,
                    low: liveData.low !== undefined ? liveData.low : null,
                    volume: liveData.volume !== undefined ? liveData.volume : null,
                    trading_date: liveData.trading_date || null,
                    is_locked: liveData.is_locked || false,
                    price_change_percent: liveData.price_change_percent !== undefined && liveData.price_change_available ? liveData.price_change_percent : (item.price_change_percent || 0),
                    price_change_available: liveData.price_change_available !== undefined ? liveData.price_change_available : (item.price_change_available || false),
                    price_arrow: liveData.price_arrow && liveData.price_change_available ? liveData.price_arrow : (item.price_arrow || "—"),
                    price_color: liveData.price_color && liveData.price_change_available ? liveData.price_color : (item.price_color || "slate"),
                    volume_percent: liveData.volume_percent !== undefined ? liveData.volume_percent : (item.volume_percent || 0),
                    amplitude_percent: liveData.amplitude_percent !== undefined ? liveData.amplitude_percent : (item.amplitude_percent || 0),
                    bctc: extraData.bctc_evaluation || extraData.bctc || item.bctc_evaluation || item.bctc || "",
                    bctc_evaluation: extraData.bctc_evaluation || extraData.bctc || item.bctc_evaluation || item.bctc || "",
                    outlook: extraData.outlook !== undefined ? extraData.outlook : item.outlook,
                    ai_recommendation: extraData.ai_recommendation !== undefined ? extraData.ai_recommendation : item.ai_recommendation,
                    ai_price_zone: extraData.ai_price_zone !== undefined ? extraData.ai_price_zone : item.ai_price_zone,
                    macro_view: extraData.macro_view !== undefined ? extraData.macro_view : item.macro_view,
                    ai_updated_at: extraData.ai_updated_at !== undefined ? extraData.ai_updated_at : item.ai_updated_at,
                    ai_source: extraData.ai_source !== undefined ? extraData.ai_source : (item.ai_source || ""),
                    fair_value_low: extraData.fair_value_low !== undefined ? extraData.fair_value_low : (item.fair_value_low || 0),
                    fair_value_high: extraData.fair_value_high !== undefined ? extraData.fair_value_high : (item.fair_value_high || 0),
                    valuation_verdict: extraData.valuation_verdict !== undefined ? extraData.valuation_verdict : (item.valuation_verdict || ""),
                    discount_to_fair_pct: extraData.discount_to_fair_pct !== undefined ? extraData.discount_to_fair_pct : (item.discount_to_fair_pct || 0),
                    margin_of_safety_pct: extraData.margin_of_safety_pct !== undefined ? extraData.margin_of_safety_pct : (item.margin_of_safety_pct || 0),
                    fair_value_rationale: extraData.fair_value_rationale !== undefined ? extraData.fair_value_rationale : (item.fair_value_rationale || ""),
                    sub_sector: extraData.sub_sector !== undefined ? extraData.sub_sector : (item.sub_sector || ""),
                    final_decision: item.final_decision !== undefined ? item.final_decision : (extraData.final_decision || ""),
                    final_decision_color: item.final_decision_color !== undefined ? item.final_decision_color : (extraData.final_decision_color || "slate"),
                    final_decision_reason: item.final_decision_reason !== undefined ? item.final_decision_reason : (extraData.final_decision_reason || ""),
                };
            });
            renderCards();
        } catch (error) {
            const container = document.getElementById('stock-container');
            if (container && showSpinner) {
                container.innerHTML = `<div class="col-span-full text-center py-8 text-rose-400 font-semibold bg-rose-500/10 rounded-xl border border-rose-500/30">⚠️ Chưa có file screener_results.json hoặc data.json!</div>`;
            }
        } finally {
            if (showSpinner && icon) icon.classList.remove('spinner');
        }
    }

    // ══════════════════════════════════════════════════
    // MODAL AI
    // ══════════════════════════════════════════════════
    function switchAiTab(tabName) {
        currentActiveTab = tabName;
        ['eval', 'simulator'].forEach(t => {
            const contentEl = document.getElementById(`tab-content-${t}`);
            const btnEl = document.getElementById(`tab-btn-${t}`);
            if (contentEl) contentEl.classList.add('hidden');
            if (btnEl) btnEl.className = "px-4 py-2 text-xs font-bold text-slate-400 hover:text-white transition";
        });
        const activeContent = document.getElementById(`tab-content-${tabName}`);
        const activeBtn = document.getElementById(`tab-btn-${tabName}`);
        if (activeContent) activeContent.classList.remove('hidden');
        if (activeBtn) activeBtn.className = "px-4 py-2 text-xs font-bold text-emerald-400 border-b-2 border-emerald-500 transition";
        if (tabName === 'simulator') calculateModalSimulation();
    }

    function openModal(symbol) {
        currentSymbol = symbol;
        const item = screenerResults.find(s => s.symbol === symbol);
        if (!item) return;

        switchAiTab(currentActiveTab);
        document.getElementById('modal-symbol-input').value = item.symbol;
        document.getElementById('modal-sector').innerText = `Ngành: ${SECTOR_NAMES[item.sector] || item.sector}`;
        document.getElementById('modal-price').innerText = formatPrice(item.close_price || item.close);
        document.getElementById('modal-company-name').innerText = item.company_name || '—';
        updateModalWatchlistBtn(item.symbol);

        const cheapBadgeContainer = document.getElementById('modal-cheap-badge-container');
        if (cheapSymbolsSet.has(item.symbol)) {
            cheapBadgeContainer.innerHTML = `<span class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold px-2 py-1 rounded-lg flex items-center gap-1.5 shadow"><i class="fa-solid fa-gem text-emerald-400"></i> Doanh nghiệp định giá rẻ</span>`;
        } else {
            cheapBadgeContainer.innerHTML = '';
        }

        document.getElementById('modal-pe').innerText = item.pe > 0 ? item.pe.toFixed(1) : '—';
        document.getElementById('modal-pb').innerText = item.pb > 0 ? item.pb.toFixed(1) : '—';
        document.getElementById('modal-eps').innerText = item.eps ? formatNumber(item.eps) : '—';
        document.getElementById('modal-roe').innerText = item.roe ? formatPercent(item.roe) : '—';
        document.getElementById('modal-roa').innerText = item.roa ? formatPercent(item.roa) : '—';
        document.getElementById('modal-div').innerText = item.dividend_yield ? item.dividend_yield + '%' : '—';

        const shares = item.total_shares || 0;
        if (shares > 0) {
            document.getElementById('modal-shares').innerText = (shares / 1_000_000).toLocaleString('vi-VN', {maximumFractionDigits: 1}) + ' Tr';
            const normalizedPrice = (item.close_price > 0 && item.close_price < 1000) ? item.close_price * 1000 : item.close_price;
            const mktCap = (shares * normalizedPrice) / 1_000_000_000;
            document.getElementById('modal-mktcap').innerText = mktCap.toLocaleString('vi-VN', {maximumFractionDigits: 0}) + ' Tỷ';
        } else {
            document.getElementById('modal-shares').innerText = '—';
            document.getElementById('modal-mktcap').innerText = '—';
        }

        const isBankOrSec = (item.sector === "NGAN_HANG" || item.sector === "CHUNG_KHOAN");
        document.getElementById('modal-cfo').innerText = (item.cfo_latest !== undefined && item.cfo_latest !== null) ? item.cfo_latest + ' Tỷ' : '—';
        document.getElementById('modal-ttm').innerText = (item.net_profit_ttm !== undefined && item.net_profit_ttm !== null) ? item.net_profit_ttm + ' Tỷ' : '—';

        const deLabel = document.getElementById('label-de');
        const deVal = document.getElementById('modal-de');
        if (isBankOrSec) {
            deLabel.innerText = "Hệ số T.Sản/VCSH";
            deVal.innerText = (item.debt_to_equity !== undefined && item.debt_to_equity !== null) ? item.debt_to_equity + 'x (Nợ/VCSH)' : '—';
        } else {
            deLabel.innerText = "Đòn bẩy D/E";
            deVal.innerText = (item.debt_to_equity !== undefined && item.debt_to_equity !== null) ? item.debt_to_equity : '—';
        }

        const gmLabel = document.getElementById('label-gm');
        const gmVal = document.getElementById('modal-gm');
        if (isBankOrSec) {
            gmLabel.innerText = "Đặc thù ngành";
            gmVal.innerText = "N/A (Ngành tài chính)";
        } else {
            gmLabel.innerText = "Biên gộp";
            gmVal.innerText = (item.gross_margin !== undefined && item.gross_margin !== null) ? item.gross_margin + '%' : '—';
        }

        const finalEl = document.getElementById('modal-final-decision');
        if (finalEl) {
            const fd = item.final_decision || "";
            const fc = item.final_decision_color || "slate";
            const fr = item.final_decision_reason || "";
            const cm = FINAL_DECISION_STYLE[fc] || FINAL_DECISION_STYLE.slate;
            if (fd) {
                finalEl.innerHTML = `
                    <div class="${cm.bg} ${cm.border} border rounded-xl p-3 space-y-1.5">
                        <div class="flex items-center justify-between gap-2 flex-wrap">
                            <div class="flex items-center gap-2">
                                <i class="fa-solid ${cm.icon} ${cm.text} text-xl"></i>
                                <div>
                                    <div class="text-[10px] text-slate-400 uppercase font-semibold">Khuyến nghị cuối cùng</div>
                                    <div class="${cm.text} text-base font-black">${fd}</div>
                                </div>
                            </div>
                            <div class="text-right text-[10px] text-slate-400 space-y-0.5">
                                <div>PTCB: <strong class="text-emerald-300">${item.fundamental_score || 0}/50</strong></div>
                                <div>PTKT: <strong class="text-indigo-300">${item.technical_score || 0}/20</strong></div>
                                <div>Định giá: <strong class="text-blue-300">${item.valuation_score || 0}/30</strong></div>
                                <div>Tổng: <strong class="text-amber-300">${item.total_score || 0}/100</strong></div>
                            </div>
                        </div>
                        <div class="text-[11px] text-slate-300 leading-relaxed pt-1.5 border-t border-slate-800/60">
                            <i class="fa-solid fa-quote-left text-slate-500 mr-1 text-[9px]"></i>${fr}
                        </div>
                    </div>
                `;
            } else {
                finalEl.innerHTML = '';
            }
        }

        const fairLow = item.fair_value_low || 0;
        const fairHigh = item.fair_value_high || 0;
        const verdict = item.valuation_verdict || "";
        const discountPct = item.discount_to_fair_pct || 0;
        const mosPct = item.margin_of_safety_pct || 0;
        const closeNow = item.close_price || 0;

        const fairZoneEl = document.getElementById('modal-fair-zone');
        if (fairZoneEl) {
            if (fairLow > 0 && fairHigh > 0) {
                let verdictColor = "text-slate-300 bg-slate-800 border-slate-700";
                let verdictIcon = "fa-circle-info";
                if (verdict.includes("RẺ")) { verdictColor = "text-emerald-300 bg-emerald-500/15 border-emerald-500/40"; verdictIcon = "fa-circle-check"; }
                else if (verdict.includes("HỢP LÝ")) { verdictColor = "text-amber-300 bg-amber-500/15 border-amber-500/40"; verdictIcon = "fa-scale-balanced"; }
                else if (verdict.includes("HƠI ĐẮT") || verdict.includes("ĐẮT")) { verdictColor = "text-rose-300 bg-rose-500/15 border-rose-500/40"; verdictIcon = "fa-hourglass-half"; }

                fairZoneEl.innerHTML = `
                    <div class="bg-gradient-to-br from-indigo-500/10 to-emerald-500/10 border border-indigo-500/30 rounded-xl p-3 space-y-2">
                        <div class="flex items-center justify-between flex-wrap gap-2">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-indigo-300">
                                <i class="fa-solid fa-crosshairs mr-1.5"></i> Vùng Mua Hợp Lý (Deterministic)
                            </h4>
                            <span class="text-[10px] px-2 py-0.5 rounded border font-bold ${verdictColor}">
                                <i class="fa-solid ${verdictIcon} mr-1"></i>${verdict}
                            </span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-center">
                            <div class="bg-slate-950/60 p-2 rounded border border-slate-800">
                                <span class="text-[10px] text-slate-400 block">Giá hiện tại</span>
                                <span class="text-sm font-bold text-white">${formatPrice(closeNow)}</span>
                            </div>
                            <div class="bg-emerald-500/10 p-2 rounded border border-emerald-500/30">
                                <span class="text-[10px] text-emerald-400 block">Vùng mua (fair_low)</span>
                                <span class="text-sm font-bold text-emerald-300">≤ ${formatPrice(fairLow)}</span>
                            </div>
                            <div class="bg-indigo-500/10 p-2 rounded border border-indigo-500/30">
                                <span class="text-[10px] text-indigo-400 block">Fair value (fair_high)</span>
                                <span class="text-sm font-bold text-indigo-300">${formatPrice(fairHigh)}</span>
                            </div>
                        </div>
                        <div class="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60">
                            <span>Biên an toàn: <strong class="text-amber-400">${mosPct}%</strong></span>
                            <span>Chiết khấu: <strong class="${discountPct > 0 ? 'text-emerald-400' : 'text-rose-400'}">${discountPct > 0 ? '+' : ''}${discountPct.toFixed(1)}%</strong></span>
                        </div>
                    </div>
                `;
            } else {
                fairZoneEl.innerHTML = `<div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3 text-center text-xs text-slate-500"><i class="fa-solid fa-hourglass-half mr-1"></i> Chưa có dữ liệu vùng mua — chạy screener.py trước.</div>`;
            }
        }

        document.getElementById('modal-ai-rec').innerText = item.ai_recommendation || item.technical_status || 'Tích lũy';
        let priceZoneText = item.ai_price_zone;
        if (typeof priceZoneText === 'object' && priceZoneText !== null) {
            priceZoneText = priceZoneText.text || priceZoneText.detail || priceZoneText.strategy || JSON.stringify(priceZoneText);
        }
        document.getElementById('modal-ai-price').innerText = priceZoneText || item.potential_zone || '—';

        const aiSourceEl = document.getElementById('modal-ai-source');
        if (aiSourceEl) {
            const src = item.ai_source || "";
            if (src === "AI" || src === "auto-ai") {
                aiSourceEl.className = "text-[9px] px-2 py-0.5 rounded border font-bold bg-indigo-500/20 text-indigo-300 border-indigo-500/40";
                aiSourceEl.innerHTML = `<i class="fa-solid fa-robot mr-1"></i>AI`;
                aiSourceEl.classList.remove('hidden');
            } else if (src === "TEMPLATE_FALLBACK" || src === "auto-template") {
                aiSourceEl.className = "text-[9px] px-2 py-0.5 rounded border font-bold bg-slate-700/40 text-slate-300 border-slate-600/50";
                aiSourceEl.innerHTML = `<i class="fa-solid fa-file-lines mr-1"></i>Template`;
                aiSourceEl.classList.remove('hidden');
            } else {
                aiSourceEl.classList.add('hidden');
            }
        }

        document.getElementById('modal-bctc').innerText = item.bctc_evaluation || item.bctc || "Chưa có đánh giá chi tiết về sức khỏe BCTC.";
        document.getElementById('modal-outlook').innerText = item.outlook || "Chưa có đánh giá triển vọng và định giá.";
        document.getElementById('modal-macro').innerText = item.macro_view || "Chưa có góc nhìn vĩ mô.";

        document.getElementById('modal-time').innerText = `AI phân tích lúc: ${item.ai_updated_at || 'Chưa chạy AI'}`;
        document.getElementById('modal-price-time').innerText = `Giá cập nhật lúc: ${item.updated_at || 'Chưa cập nhật'}`;

        let histRate = 15;
        if (symbolSimRates[symbol] && symbolSimRates[symbol].annual_rate_percent !== undefined) {
            histRate = symbolSimRates[symbol].annual_rate_percent;
            document.getElementById('sim-historical-rate-text').innerText = histRate + "% / năm (Quá khứ thực tế)";
        } else {
            document.getElementById('sim-historical-rate-text').innerText = "15% / năm (Mức chuẩn cơ sở)";
        }
        const details = quarterlyMeanDetails[symbol];
        if (details) {
            document.getElementById('sim-start-quarter-info').innerText = `${details.start_quarter}: ${formatPrice(details.start_price_mean)} đ`;
            document.getElementById('sim-end-quarter-info').innerText = `${details.end_quarter}: ${formatPrice(details.end_price_mean)} đ`;
        } else {
            document.getElementById('sim-start-quarter-info').innerText = "Không có dữ liệu";
            document.getElementById('sim-end-quarter-info').innerText = "Không có dữ liệu";
        }

        document.getElementById('modal-sim-rate').value = histRate;
        document.getElementById('modal-sim-initial').value = "20.000.000";
        document.getElementById('modal-sim-monthly').value = "3.000.000";
        document.getElementById('modal-sim-years').value = "3";

        document.getElementById('ai-modal').classList.remove('hidden');
    }

    function closeModal() { document.getElementById('ai-modal').classList.add('hidden'); }

    function navigateModalSymbol(direction) {
        const symbols = screenerResults.map(s => s.symbol).sort();
        const currentIndex = symbols.indexOf(currentSymbol);
        if (currentIndex !== -1) {
            let newIndex = currentIndex + direction;
            if (newIndex < 0) newIndex = symbols.length - 1;
            if (newIndex >= symbols.length) newIndex = 0;
            openModal(symbols[newIndex]);
        }
    }

    let currentModalSuggestions = [];
    function handleModalSearchInput(val) {
        const term = val.trim().toUpperCase();
        const suggestBox = document.getElementById('modal-search-suggestions');
        if (!term) { suggestBox.classList.add('hidden'); return; }
        currentModalSuggestions = screenerResults.filter(item => item.symbol.includes(term)).slice(0, 8);
        if (currentModalSuggestions.length === 0) {
            suggestBox.innerHTML = `<div class="px-2 py-1.5 text-xs text-slate-500">Không tìm thấy.</div>`;
            suggestBox.classList.remove('hidden');
        } else {
            let html = '';
            currentModalSuggestions.forEach(item => {
                html += `<button type="button" onclick="selectModalSuggestion('${item.symbol}')" class="w-full text-left px-2 py-1.5 rounded-lg text-xs font-bold transition flex justify-between items-center hover:bg-slate-800 text-slate-300"><span>${item.symbol}</span></button>`;
            });
            suggestBox.innerHTML = html;
            suggestBox.classList.remove('hidden');
        }
    }

    function handleModalSearchKeyDown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            if (currentModalSuggestions.length > 0) selectModalSuggestion(currentModalSuggestions[0].symbol);
        }
    }

    function selectModalSuggestion(symbol) {
        document.getElementById('modal-search-suggestions').classList.add('hidden');
        document.getElementById('modal-symbol-input').value = symbol;
        openModal(symbol);
    }

    window.addEventListener('click', (e) => {
        const modalSearchBox = document.getElementById('modal-symbol-input');
        const modalSuggest = document.getElementById('modal-search-suggestions');
        if (modalSearchBox && modalSuggest && !modalSearchBox.contains(e.target) && !modalSuggest.contains(e.target)) {
            modalSuggest.classList.add('hidden');
        }
    });

    function calculateModalSimulation() {
        let p0 = parseCleanNumber(document.getElementById('modal-sim-initial').value);
        let pMonthly = parseCleanNumber(document.getElementById('modal-sim-monthly').value);
        let years = parseFloat(document.getElementById('modal-sim-years').value) || 1;
        let rate = (parseFloat(document.getElementById('modal-sim-rate').value) || 15) / 100;
        let totalPrincipal = p0 + (pMonthly * 12 * years);
        let futureVal = p0 * Math.pow(1 + rate, years);
        let monthlyRate = rate / 12;
        let totalMonths = years * 12;
        for (let i = 1; i <= totalMonths; i++) {
            futureVal += pMonthly * Math.pow(1 + monthlyRate, totalMonths - i + 1);
        }
        let profit = futureVal - totalPrincipal;
        document.getElementById('modal-sim-principal').innerText = Math.round(totalPrincipal).toLocaleString("vi-VN") + " VNĐ";
        document.getElementById('modal-sim-profit').innerText = "+" + Math.round(profit).toLocaleString("vi-VN") + " VNĐ";
        document.getElementById('modal-sim-total').innerText = Math.round(futureVal).toLocaleString("vi-VN") + " VNĐ";
    }

    // ══════════════════════════════════════════════════
    // CHART
    // ══════════════════════════════════════════════════
    function navigateSymbol(direction) {
        const symbols = screenerResults.map(s => s.symbol).sort();
        const currentIndex = symbols.indexOf(currentSymbol);
        if (currentIndex !== -1) {
            let newIndex = currentIndex + direction;
            if (newIndex < 0) newIndex = symbols.length - 1;
            if (newIndex >= symbols.length) newIndex = 0;
            openChartModal(symbols[newIndex]);
        }
    }

    function toggleSymbolDropdown() {
        const dropdown = document.getElementById('symbol-dropdown');
        dropdown.classList.toggle('hidden');
        if (!dropdown.classList.contains('hidden')) {
            document.getElementById('dropdown-search').value = '';
            renderDropdownSymbolList(screenerResults.map(s => s.symbol));
            document.getElementById('dropdown-search').focus();
        }
    }

    function renderDropdownSymbolList(symbols) {
        const listContainer = document.getElementById('dropdown-symbol-list');
        listContainer.innerHTML = '';
        symbols.sort().forEach(sym => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = `w-full text-left px-2 py-1 rounded-lg text-xs font-bold transition flex justify-between items-center ${sym === currentSymbol ? 'bg-emerald-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`;
            item.innerHTML = `<span>${sym}</span>`;
            item.onclick = (e) => {
                e.stopPropagation();
                document.getElementById('symbol-dropdown').classList.add('hidden');
                openChartModal(sym);
            };
            listContainer.appendChild(item);
        });
    }

    function filterDropdownSymbols(keyword) {
        const upper = keyword.toUpperCase();
        const matched = screenerResults.map(s => s.symbol).filter(sym => sym.includes(upper));
        renderDropdownSymbolList(matched);
    }

    function handleDropdownSearchKeyDown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const firstBtn = document.querySelector('#dropdown-symbol-list button');
            if (firstBtn) firstBtn.click();
        }
    }

    window.addEventListener('click', (e) => {
        const dropdown = document.getElementById('symbol-dropdown');
        const symbolBtn = document.getElementById('chart-modal-symbol');
        if (dropdown && !dropdown.contains(e.target) && !symbolBtn.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });

    function switchInterval(interval) {
        currentInterval = interval;
        ['d1', 'w1', 'mn'].forEach(i => {
            const btn = document.getElementById(`btn-${i}`);
            if (btn) {
                btn.className = i === interval.toLowerCase()
                    ? "px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition"
                    : "px-1.5 py-0.5 text-[10px] font-bold rounded text-slate-400 hover:text-white transition";
            }
        });
        if (currentSymbolHistory) renderChartInstance(currentSymbolHistory);
    }

    function toggleIndicator(name) {
        activeIndicators[name] = !activeIndicators[name];
        const btn = document.getElementById(`btn-ind-${name.toLowerCase()}`);
        if (btn) {
            btn.className = activeIndicators[name]
                ? "px-1.5 py-0.5 text-[9px] font-bold rounded bg-indigo-600 text-white border border-indigo-400/50 transition"
                : "px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition";
        }
        if (currentSymbolHistory) renderChartInstance(currentSymbolHistory);
    }

    function toggleQuarterLines() {
        activeIndicators.QLINES = !activeIndicators.QLINES;
        const btn = document.getElementById('btn-ind-qlines');
        if (btn) {
            btn.className = activeIndicators.QLINES
                ? "px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition ml-1"
                : "px-1.5 py-0.5 text-[10px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition ml-1";
        }
        if (currentSymbolHistory) renderChartInstance(currentSymbolHistory);
    }

    function toggleQuarterZone() {
        activeIndicators.QZONE = !activeIndicators.QZONE;
        const btn = document.getElementById('btn-ind-qzone');
        if (btn) {
            btn.className = activeIndicators.QZONE
                ? "px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-600 text-white transition"
                : "px-1.5 py-0.5 text-[10px] font-bold rounded bg-slate-900/40 text-slate-400 hover:text-white transition";
        }
        if (currentSymbolHistory) renderChartInstance(currentSymbolHistory);
    }

    function jumpToQuarter(type) {
        const details = quarterlyMeanDetails[currentSymbol];
        if (!details || !currentSymbolHistory) return;
        let chartData = [];
        if (currentInterval === 'D1') chartData = currentSymbolHistory.history_d1 || [];
        else if (currentInterval === 'W1') chartData = currentSymbolHistory.history_w1 || [];
        else if (currentInterval === 'MN') chartData = currentSymbolHistory.history_mn || [];
        const quarterStr = (type === 'start') ? details.start_quarter : details.end_quarter;
        if (!quarterStr) return;
        const parts = quarterStr.split('Q');
        const year = parseInt(parts[0]);
        const q = parseInt(parts[1]);
        const startMonth = (q - 1) * 3 + 1;
        const endMonth = q * 3;
        let indices = [];
        let qMinPrice = Infinity, qMaxPrice = -Infinity;
        chartData.forEach((bar, idx) => {
            const barDate = new Date(bar.time);
            if (barDate.getFullYear() === year && (barDate.getMonth() + 1) >= startMonth && (barDate.getMonth() + 1) <= endMonth) {
                indices.push(idx);
                if (bar.low < qMinPrice) qMinPrice = bar.low;
                if (bar.high > qMaxPrice) qMaxPrice = bar.high;
            }
        });
        if (indices.length > 0 && chartInstance) {
            const minIdx = indices[0];
            const maxIdx = indices[indices.length - 1];
            chartInstance.priceScale('right').applyOptions({ autoScale: true });
            const rangeSpan = Math.max(15, (maxIdx - minIdx) * 2);
            const from = Math.max(0, minIdx - Math.floor(rangeSpan / 2));
            const to = Math.min(chartData.length - 1, maxIdx + Math.floor(rangeSpan / 2));
            chartInstance.timeScale().setVisibleLogicalRange({ from, to });
            if (qMinPrice !== Infinity && qMaxPrice !== -Infinity) {
                const pricePadding = (qMaxPrice - qMinPrice) * 0.5;
                chartInstance.priceScale('right').setVisiblePriceRange({ from: qMinPrice - pricePadding, to: qMaxPrice + pricePadding });
            }
        } else {
            alert(`Không tìm thấy dữ liệu thời gian cho ${quarterStr}!`);
        }
    }

    function resizeChart() {
        if (chartInstance) {
            const container = document.getElementById('tv-chart-container');
            if (container) chartInstance.applyOptions({ width: container.clientWidth, height: container.clientHeight });
        }
    }

    function toggleFullscreen() {
        const modalBox = document.getElementById('chart-modal-box');
        const fsBtnIcon = document.querySelector('#fullscreen-btn i');
        modalBox.classList.toggle('fullscreen');
        fsBtnIcon.className = modalBox.classList.contains('fullscreen') ? "fa-solid fa-compress text-xs" : "fa-solid fa-expand text-xs";
        setTimeout(resizeChart, 200);
    }

    window.addEventListener('resize', () => {
        if (!document.getElementById('chart-modal').classList.contains('hidden')) setTimeout(resizeChart, 300);
    });

    function closeChartModal() {
        document.getElementById('chart-modal').classList.add('hidden');
        if (chartInstance) { chartInstance.remove(); chartInstance = null; }
        currentSymbolHistory = null;
    }

    async function openChartModal(symbol) {
        currentSymbol = symbol;
        currentInterval = 'D1';
        switchInterval('D1');
        document.getElementById('current-symbol-text').innerText = symbol;
        document.getElementById('symbol-dropdown').classList.add('hidden');
        document.getElementById('btn-view-ai').onclick = () => { closeChartModal(); openModal(symbol); };
        updateChartWatchlistBtn(symbol);

        const item = screenerResults.find(s => s.symbol === symbol);
        if (item && item.updated_at) {
            const cleanTime = item.updated_at.replace(/\s*\(.*?\)\s*/g, '').trim();
            document.getElementById('chart-last-update').innerText = cleanTime;
        } else {
            document.getElementById('chart-last-update').innerText = "Chưa rõ";
        }

        document.getElementById('chart-modal').classList.remove('hidden');
        document.getElementById('chart-loading').classList.remove('hidden');

        try {
            const res = await fetch(`history/${symbol}.json?t=` + new Date().getTime());
            if (!res.ok) throw new Error("Không tìm thấy file");
            currentSymbolHistory = await res.json();

            if (currentSymbolHistory.history_d1) {
                currentSymbolHistory.history_d1 = currentSymbolHistory.history_d1
                    .filter(bar => bar.time && bar.open > 0 && bar.high > 0 && bar.low > 0 && bar.close > 0)
                    .map(bar => ({
                        time: bar.time, open: bar.open * 1000, high: bar.high * 1000, low: bar.low * 1000, close: bar.close * 1000, volume: bar.volume
                    }));
            } else {
                currentSymbolHistory.history_d1 = [];
            }

            if (currentSymbolHistory.history_w1) {
                currentSymbolHistory.history_w1 = currentSymbolHistory.history_w1
                    .filter(bar => bar.time && bar.open > 0 && bar.high > 0 && bar.low > 0 && bar.close > 0)
                    .map(bar => ({
                        time: bar.time, open: bar.open * 1000, high: bar.high * 1000, low: bar.low * 1000, close: bar.close * 1000, volume: bar.volume
                    }));
            }

            if (currentSymbolHistory.history_mn) {
                currentSymbolHistory.history_mn = currentSymbolHistory.history_mn
                    .filter(bar => bar.time && bar.open > 0 && bar.high > 0 && bar.low > 0 && bar.close > 0)
                    .map(bar => ({
                        time: bar.time, open: bar.open * 1000, high: bar.high * 1000, low: bar.low * 1000, close: bar.close * 1000, volume: bar.volume
                    }));
            }

            let currentPrice = item ? (item.close_price !== undefined ? item.close_price : item.close) : 0;
            const tradingDate = item && item.trading_date ? item.trading_date : null;

            let itemOpen = item.open || 0;
            let itemHigh = item.high || 0;
            let itemLow = item.low || 0;
            let itemVolume = item.volume || 0;

            if (currentPrice > 0 && currentPrice < 1000) currentPrice *= 1000;
            if (itemOpen > 0 && itemOpen < 1000) itemOpen *= 1000;
            if (itemHigh > 0 && itemHigh < 1000) itemHigh *= 1000;
            if (itemLow > 0 && itemLow < 1000) itemLow *= 1000;

            if (currentPrice > 0 && currentSymbolHistory.history_d1.length > 0) {
                const lastBar = currentSymbolHistory.history_d1[currentSymbolHistory.history_d1.length - 1];
                const effectiveDate = tradingDate || lastBar.time;
                const existingBar = currentSymbolHistory.history_d1.find(b => b.time === effectiveDate);

                if (existingBar) {
                    existingBar.close = currentPrice;
                    if (itemHigh > 0) existingBar.high = Math.max(existingBar.high, itemHigh);
                    if (itemLow > 0)  existingBar.low  = Math.min(existingBar.low, itemLow);
                    if (itemVolume > 0) existingBar.volume = itemVolume;
                } else {
                    const recentBars = currentSymbolHistory.history_d1.slice(-20);
                    let sumVol = 0;
                    recentBars.forEach(b => { sumVol += (b.volume || 0); });
                    const avgVol20 = recentBars.length > 0 ? (sumVol / recentBars.length) : 0;
                    const isVolumeEnough = avgVol20 > 0 ? (itemVolume >= avgVol20 * 0.2) : true;

                    if (isVolumeEnough) {
                        const hasValidOHLC = itemOpen > 0 && itemHigh > 0 && itemLow > 0;
                        if (hasValidOHLC) {
                            let liveVolume = itemVolume;
                            if (!liveVolume || liveVolume < 1000) liveVolume = lastBar.volume;
                            currentSymbolHistory.history_d1.push({
                                time: effectiveDate, open: itemOpen, high: itemHigh, low: itemLow, close: currentPrice, volume: liveVolume
                            });
                        }
                    }
                }
            }

            currentSymbolHistory.history_d1.sort((a, b) => a.time.localeCompare(b.time));
            renderChartInstance(currentSymbolHistory);

        } catch (err) {
            console.error("Lỗi tải biểu đồ:", err);
            document.getElementById('tv-chart-container').innerHTML = `<div class="flex items-center justify-center h-full text-rose-400 text-xs">Chưa có dữ liệu lịch sử cho mã này!</div>`;
        } finally {
            document.getElementById('chart-loading').classList.add('hidden');
        }
    }

    function calculateMA(data, period) {
        let result = [];
        for (let i = 0; i < data.length; i++) {
            if (i < period - 1) continue;
            let sum = 0;
            for (let j = 0; j < period; j++) sum += data[i - j].close;
            result.push({ time: data[i].time, value: sum / period });
        }
        return result;
    }

    function calculateVolumeMA(data, period = 20) {
        let result = [];
        for (let i = 0; i < data.length; i++) {
            if (i < period - 1) continue;
            let sum = 0;
            for (let j = 0; j < period; j++) sum += data[i - j].volume;
            result.push({ time: data[i].time, value: sum / period });
        }
        return result;
    }

    function calculateRSI(data, period = 14) {
        let result = [];
        let gains = 0, losses = 0;
        for (let i = 1; i < data.length; i++) {
            let change = data[i].close - data[i - 1].close;
            if (i <= period) {
                if (change >= 0) gains += change; else losses -= change;
                if (i === period) {
                    let avgGain = gains / period, avgLoss = losses / period;
                    let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
                    result.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) });
                }
            } else {
                gains = (gains * (period - 1) + (change >= 0 ? change : 0)) / period;
                losses = (losses * (period - 1) + (change < 0 ? -change : 0)) / period;
                let rs = losses === 0 ? 100 : gains / losses;
                result.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) });
            }
        }
        return result;
    }

    function renderChartInstance(historyDataObj) {
        const container = document.getElementById('tv-chart-container');
        container.innerHTML = '';
        const LC = window.LightweightCharts;
        if (!LC) return;
        const width = container.clientWidth || 600;
        const height = container.clientHeight || 380;
        const hasRSI = activeIndicators.RSI;

        chartInstance = LC.createChart(container, {
            width: width, height: height,
            layout: { background: { type: 'solid', color: '#0f172a' }, textColor: '#94a3b8' },
            grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
            timeScale: { borderColor: '#334155' }
        });

        candleSeriesInstance = chartInstance.addSeries(LC.CandlestickSeries, {
            upColor: '#10b981', downColor: '#f43f5e', borderUpColor: '#10b981', borderDownColor: '#f43f5e', wickUpColor: '#10b981', wickDownColor: '#f43f5e',
        }, 0);

        volumeSeriesInstance = chartInstance.addSeries(LC.HistogramSeries, {
            priceFormat: { type: 'volume' }, priceScaleId: 'volumeScale'
        }, 0);

        chartInstance.priceScale('volumeScale').applyOptions({ scaleMargins: { top: 0.8, bottom: 0.05 } });

        let chartData = [];
        if (currentInterval === 'D1') chartData = historyDataObj.history_d1 || [];
        else if (currentInterval === 'W1') chartData = historyDataObj.history_w1 || [];
        else if (currentInterval === 'MN') chartData = historyDataObj.history_mn || [];

        let maxVol = 0;
        const recentBars = chartData.slice(-20);
        recentBars.forEach(bar => {
            if (bar.volume > maxVol) maxVol = bar.volume;
        });

        if (maxVol > 0) {
            volumeSeriesInstance.applyOptions({
                autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: maxVol * 1.2 } })
            });
        }

        if (chartData && chartData.length > 0) {
            candleSeriesInstance.setData(chartData);
            volumeSeriesInstance.setData(chartData.map(row => ({
                time: row.time, value: row.volume, color: row.close >= row.open ? 'rgba(16, 185, 129, 0.5)' : 'rgba(244, 63, 94, 0.5)'
            })));

            const details = quarterlyMeanDetails[currentSymbol];
            if (details) {
                function getQuarterBoxInfo(quarterStr, allBars) {
                    if (!quarterStr) return null;
                    const parts = quarterStr.split('Q');
                    const year = parseInt(parts[0]);
                    const q = parseInt(parts[1]);
                    const startMonth = (q - 1) * 3 + 1;
                    const endMonth = q * 3;
                    const quarterBars = allBars.filter(bar => {
                        const barDate = new Date(bar.time);
                        return barDate.getFullYear() === year && (barDate.getMonth() + 1) >= startMonth && (barDate.getMonth() + 1) <= endMonth;
                    });
                    if (quarterBars.length === 0) return null;
                    let qHigh = -Infinity, qLow = Infinity;
                    quarterBars.forEach(b => { if (b.high > qHigh) qHigh = b.high; if (b.low < qLow) qLow = b.low; });
                    return { high: qHigh, low: qLow, data: quarterBars.map(row => ({ time: row.time, value: qHigh, baseValue: qLow })) };
                }

                if (activeIndicators.QZONE) {
                    const startBoxInfo = getQuarterBoxInfo(details.start_quarter, chartData);
                    if (startBoxInfo && startBoxInfo.data.length > 0) {
                        const startBoxSeries = chartInstance.addSeries(LC.BaselineSeries, {
                            baseValue: { type: 'price', price: startBoxInfo.low }, topFillColor1: 'rgba(59, 130, 246, 0.45)', topFillColor2: 'rgba(59, 130, 246, 0.15)', topLineColor: '#2563eb', bottomLineColor: '#2563eb', lineWidth: 2
                        }, 0);
                        startBoxSeries.setData(startBoxInfo.data);
                    }
                    const endBoxInfo = getQuarterBoxInfo(details.end_quarter, chartData);
                    if (endBoxInfo && endBoxInfo.data.length > 0) {
                        const endBoxSeries = chartInstance.addSeries(LC.BaselineSeries, {
                            baseValue: { type: 'price', price: endBoxInfo.low }, topFillColor1: 'rgba(16, 185, 129, 0.45)', topFillColor2: 'rgba(16, 185, 129, 0.15)', topLineColor: '#059669', bottomLineColor: '#059669', lineWidth: 2
                        }, 0);
                        endBoxSeries.setData(endBoxInfo.data);
                    }
                }

                if (activeIndicators.QLINES) {
                    let startPrice = details.start_price_mean;
                    if (startPrice > 0 && startPrice < 1000) startPrice = startPrice * 1000;
                    let endPrice = details.end_price_mean;
                    if (endPrice > 0 && endPrice < 1000) endPrice = endPrice * 1000;
                    candleSeriesInstance.createPriceLine({ price: startPrice, color: '#f97316', lineWidth: 2, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: true, title: `Q.Đầu 5Y (${details.start_quarter}): ${formatNumber(startPrice)}` });
                    candleSeriesInstance.createPriceLine({ price: endPrice, color: '#10b981', lineWidth: 2, lineStyle: LC.LineStyle.Dotted, axisLabelVisible: true, title: `Q.Cuối (${details.end_quarter}): ${formatNumber(endPrice)}` });
                }
            }

            if (activeIndicators.MA20) chartInstance.addSeries(LC.LineSeries, { color: '#3b82f6', lineWidth: 1 }, 0).setData(calculateMA(chartData, 20));
            if (activeIndicators.MA50) chartInstance.addSeries(LC.LineSeries, { color: '#eab308', lineWidth: 1 }, 0).setData(calculateMA(chartData, 50));
            if (activeIndicators.VOLMA) chartInstance.addSeries(LC.LineSeries, { color: '#f97316', lineWidth: 1, priceScaleId: 'volumeScale' }, 0).setData(calculateVolumeMA(chartData, 20));
            
            if (hasRSI) {
                const rsiSeries = chartInstance.addSeries(LC.LineSeries, { color: '#a855f7', lineWidth: 1.5 }, 1);
                rsiSeries.createPriceLine({ price: 70, color: '#ef5350', lineWidth: 1, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: true });
                rsiSeries.createPriceLine({ price: 30, color: '#26a69a', lineWidth: 1, lineStyle: LC.LineStyle.Dashed, axisLabelVisible: true });
                rsiSeries.setData(calculateRSI(chartData, 14));
            }

            const legendTime = document.getElementById('legend-time');
            const legendClose = document.getElementById('legend-close');
            const legendChange = document.getElementById('legend-change');
            const legendVol = document.getElementById('legend-vol');
            const latestBar = chartData[chartData.length - 1];
            if (latestBar) updateLegend(latestBar, chartData);

            function updateLegend(bar, dataArr) {
                legendTime.innerText = bar.time;
                legendClose.innerText = formatNumber(bar.close);
                const index = dataArr.findIndex(item => item.time === bar.time);
                let changePct = 0;
                if (index > 0 && dataArr[index - 1].close > 0) {
                    changePct = ((bar.close - dataArr[index - 1].close) / dataArr[index - 1].close) * 100;
                }
                legendChange.innerText = `(${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%)`;
                legendChange.className = `font-bold ${changePct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
                legendClose.className = `font-bold ${changePct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
                legendVol.innerText = formatNumber(bar.volume);
            }

            chartInstance.subscribeCrosshairMove(param => {
                if (!param.point || !param.time) {
                    if (latestBar) updateLegend(latestBar, chartData);
                } else {
                    const dataPoint = param.seriesData.get(candleSeriesInstance);
                    if (dataPoint) updateLegend({ time: param.time, close: dataPoint.close, volume: param.seriesData.get(volumeSeriesInstance)?.value || 0 }, chartData);
                }
            });

            setTimeout(() => {
                const totalBars = chartData.length;
                let visibleBarsCount = width > 1200 ? 120 : (width > 768 ? 90 : 50);
                if (totalBars > visibleBarsCount) chartInstance.timeScale().setVisibleLogicalRange({ from: totalBars - visibleBarsCount, to: totalBars - 1 });
                else chartInstance.timeScale().fitContent();
            }, 50);
        }
    }

    // ══════════════════════════════════════════════════
    // REFRESH GIÁ
    // ══════════════════════════════════════════════════
    let isRefreshingAll = false;
    async function refreshPrices() {
        if (isRefreshingAll || isRefreshingSingle) { addLog(`Hệ thống đang bận, vui lòng đợi tiến trình hiện tại xong!`, 'warning'); return; }
        isRefreshingAll = true;
        const icon = document.getElementById('refresh-icon');
        const headerBtn = icon ? icon.closest('button') : null;
        if (icon) icon.classList.add('spinner');
        if (headerBtn) headerBtn.disabled = true;
        document.querySelectorAll('[data-refresh-single]').forEach(btn => { btn.disabled = true; btn.classList.add('opacity-50', 'cursor-not-allowed'); });
        showLogConsole();
        document.getElementById('log-content').innerHTML = '';
        updateProgress(0, 1);
        const symbols = screenerResults.map(item => item.symbol);
        if (symbols.length === 0) {
            addLog(`Danh sách trống, không có gì để cập nhật.`, 'warning');
            isRefreshingAll = false;
            if (icon) icon.classList.remove('spinner');
            if (headerBtn) headerBtn.disabled = false;
            document.querySelectorAll('[data-refresh-single]').forEach(btn => { btn.disabled = false; btn.classList.remove('opacity-50', 'cursor-not-allowed'); });
            return;
        }
        addLog(`Bắt đầu lấy giá cho ${symbols.length} mã...`, 'processing');
        updateProgress(0, symbols.length);
        try {
            const chunkSize = 20;
            const chunks = [];
            for (let i = 0; i < symbols.length; i += chunkSize) { chunks.push(symbols.slice(i, i + chunkSize)); }
            let updatedCount = 0;
            let processedCount = 0;
            let lastUpdateTime = "";
            await Promise.all(chunks.map(async (chunk) => {
                const symQuery = chunk.join(',');
                try {
                    const res = await fetch(`${PRICE_API_URL}/api/sync?symbols=${symQuery}`);
                    if (res.ok) {
                        const data = await res.json();
                        lastUpdateTime = data.updated_at.replace(/\s*\(.*?\)\s*/g, '').trim();
                        chunk.forEach(sym => {
                            if (data.updated_data && data.updated_data[sym] !== undefined) {
                                const price = data.updated_data[sym];
                                const item = screenerResults.find(s => s.symbol === sym);
                                if (item) { item.close_price = price; item.updated_at = lastUpdateTime; }
                                addLog(`${sym}: ${formatPrice(price)} đ`, 'success');
                                updatedCount++;
                            } else { addLog(`${sym}: Không lấy được giá`, 'error'); }
                            processedCount++;
                            updateProgress(processedCount, symbols.length);
                        });
                    } else {
                        chunk.forEach(sym => {
                            addLog(`${sym}: Lỗi server API (${res.status})`, 'error');
                            processedCount++;
                            updateProgress(processedCount, symbols.length);
                        });
                    }
                } catch (err) {
                    chunk.forEach(sym => {
                        addLog(`${sym}: Lỗi kết nối mạng`, 'error');
                        processedCount++;
                        updateProgress(processedCount, symbols.length);
                    });
                }
            }));
            renderCards();
            if (lastUpdateTime) { document.getElementById('header-last-update').innerText = lastUpdateTime + " (Toàn bộ)"; }
            addLog(`Hoàn tất toàn bộ! Đã cập nhật ${updatedCount}/${symbols.length} mã.`, 'success');
            updateProgress(symbols.length, symbols.length);
        } catch (err) {
            console.error(err);
            addLog(`Lỗi nghiêm trọng khi gọi API.`, 'error');
        } finally {
            isRefreshingAll = false;
            if (icon) icon.classList.remove('spinner');
            if (headerBtn) headerBtn.disabled = false;
            document.querySelectorAll('[data-refresh-single]').forEach(btn => { btn.disabled = false; btn.classList.remove('opacity-50', 'cursor-not-allowed'); });
            setTimeout(() => { if (!isLogMinimized) hideLogConsole(); }, 3000);
        }
    }

    let isRefreshingSingle = false;
    async function refreshSinglePrice(symbol, btnElement) {
        if (isRefreshingAll || isRefreshingSingle) { addLog(`Hệ thống đang bận, đợi xíu nhé!`, 'warning'); return; }
        if (btnElement.disabled) return;
        isRefreshingSingle = true;
        btnElement.disabled = true;
        const icon = btnElement.querySelector('i');
        if (icon) icon.classList.add('spinner');
        const headerBtn = document.getElementById('refresh-icon')?.closest('button');
        if (headerBtn) { headerBtn.disabled = true; headerBtn.classList.add('opacity-50', 'cursor-not-allowed'); }
        showLogConsole();
        document.getElementById('log-content').innerHTML = '';
        updateProgress(0, 1);
        addLog(`Bắt đầu lấy giá cho ${symbol}...`, 'processing');
        try {
            const res = await fetch(`${PRICE_API_URL}/api/sync?symbols=${symbol}`);
            if (res.ok) {
                const data = await res.json();
                if (data.updated_data && data.updated_data[symbol] !== undefined) {
                    const newPrice = data.updated_data[symbol];
                    const newTime = data.updated_at.replace(/\s*\(.*?\)\s*/g, '').trim();
                    const item = screenerResults.find(s => s.symbol === symbol);
                    if (item) { item.close_price = newPrice; item.updated_at = newTime; }
                    const card = btnElement.closest('.bg-slate-900');
                    if (card) {
                        const priceEl = card.querySelector('.text-emerald-400.leading-tight');
                        if (priceEl) {
                            priceEl.innerText = formatPrice(newPrice);
                            priceEl.classList.add('text-white', 'bg-emerald-500');
                            setTimeout(() => priceEl.classList.remove('text-white', 'bg-emerald-500'), 500);
                        }
                        const timeEl = card.querySelector('.fa-clock').parentElement;
                        if (timeEl) timeEl.innerHTML = `<i class="fa-regular fa-clock mr-0.5"></i>${newTime}`;
                    }
                    addLog(`${symbol}: ${formatPrice(newPrice)} đ`, 'success');
                } else {
                    addLog(`${symbol}: Không lấy được giá`, 'error');
                }
            } else { addLog(`${symbol}: Lỗi server (${res.status})`, 'error'); }
        } catch (err) { addLog(`${symbol}: Lỗi kết nối mạng`, 'error'); }
        finally {
            updateProgress(1, 1);
            isRefreshingSingle = false;
            btnElement.disabled = false;
            if (icon) icon.classList.remove('spinner');
            if (headerBtn) { headerBtn.disabled = false; headerBtn.classList.remove('opacity-50', 'cursor-not-allowed'); }
            setTimeout(() => { if (!isLogMinimized) hideLogConsole(); }, 2000);
        }
    }

    document.getElementById('search-input').addEventListener('input', renderCards);
    document.getElementById('sector-filter').addEventListener('change', renderCards);
    document.getElementById('ranking-filter').addEventListener('change', renderCards);
    """
