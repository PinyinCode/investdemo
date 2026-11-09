# -*- coding: utf-8 -*-
"""giaodien_ui.py — Module UI base."""

def build_ui_css():
    return r"""
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
        background-color: #020617; color: #f59e0b; font-weight: 700;
        font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase;
        padding: 8px 10px; border-top: 1px solid #1e293b;
    }
    #ranking-filter option {
        background-color: #0f172a; color: #e2e8f0; font-weight: 500;
        font-size: 13px; padding: 9px 12px; text-transform: none; letter-spacing: normal;
    }
    #ranking-filter option:checked {
        background: linear-gradient(90deg, #78350f 0%, #b45309 100%);
        color: #fef3c7; font-weight: 700;
    }

    #log-content::-webkit-scrollbar { width: 4px; }
    #log-content::-webkit-scrollbar-track { background: #0f172a; }
    #log-content::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }

    /* ══════════ KHÓA TRANG KHI CHƯA ĐĂNG NHẬP ══════════ */
    body.auth-locked { overflow: hidden !important; }
    body.auth-locked main, body.auth-locked header {
        filter: blur(12px);
        pointer-events: none;
        user-select: none;
    }
    """

def build_ui_js():
    return r"""
    function formatPrice(num) {
        if (num === undefined || num === null || num === 0) return '—';
        let val = num;
        if (val > 0 && val < 1000) val = val * 1000;
        return Math.round(val).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    function formatNumber(num) {
        if (num === undefined || num === null || num === 0) return '—';
        return Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    function formatPercent(num) {
        if (num === undefined || num === null) return '—';
        return num.toFixed(1) + '%';
    }
    function formatCurrencyInput(input) {
        let cursorPos = input.selectionStart;
        let originalLen = input.value.length;
        let num = parseCleanNumber(input.value);
        input.value = num.toLocaleString('vi-VN');
        let newLen = input.value.length;
        input.setSelectionRange(cursorPos + (newLen - originalLen), cursorPos + (newLen - originalLen));
    }
    function parseCleanNumber(str) {
        if (typeof str === 'number') return str;
        return parseFloat(String(str).replace(/[^0-9]/g, '')) || 0;
    }
    function clearInput(elementId) {
        const inputEl = document.getElementById(elementId);
        if (!inputEl) return;
        inputEl.value = ''; inputEl.focus();
        if (elementId === 'search-input') {
            document.getElementById('search-suggestions').classList.add('hidden');
            document.getElementById('sector-filter').value = "ALL";
            document.getElementById('ranking-filter').value = "FINAL_BUY_ONLY";
            document.getElementById('shock-filter').checked = false;
            if (typeof renderCards === 'function') renderCards();
        } else if (elementId === 'modal-symbol-input') {
            document.getElementById('modal-search-suggestions').classList.add('hidden');
        } else if (elementId === 'dropdown-search') {
            if (typeof filterDropdownSymbols === 'function') filterDropdownSymbols('');
        }
    }
    function toggleProMetrics() {
        const box = document.getElementById('pro-metrics-box');
        const textEl = document.getElementById('prometrics-text');
        const chevron = document.getElementById('prometrics-chevron');
        if (box.classList.contains('hidden')) {
            box.classList.remove('hidden');
            textEl.innerText = "Ẩn bớt chỉ số chuyên nghiệp";
            chevron.style.transform = "rotate(180deg)";
        } else {
            box.classList.add('hidden');
            textEl.innerText = "Hiển thị thêm chỉ số chuyên nghiệp (CFO, D/E, Biên gộp, TTM)";
            chevron.style.transform = "rotate(0deg)";
        }
    }
    let isLogMinimized = false, isLogVisible = false;
    function toggleLogConsole() {
        const contentEl = document.getElementById('log-content');
        const chevron = document.getElementById('log-chevron');
        isLogMinimized = !isLogMinimized;
        if (isLogMinimized) { contentEl.classList.add('hidden'); chevron.classList.replace('fa-chevron-down', 'fa-chevron-up'); }
        else { contentEl.classList.remove('hidden'); chevron.classList.replace('fa-chevron-up', 'fa-chevron-down'); contentEl.scrollTop = contentEl.scrollHeight; }
    }
    function showLogConsole() {
        if (isLogVisible) return;
        isLogVisible = true; isLogMinimized = false;
        const consoleEl = document.getElementById('log-console');
        const contentEl = document.getElementById('log-content');
        const chevron = document.getElementById('log-chevron');
        consoleEl.classList.remove('hidden', 'translate-y-full', 'opacity-0');
        contentEl.classList.remove('hidden');
        if (chevron) chevron.classList.replace('fa-chevron-up', 'fa-chevron-down');
    }
    function hideLogConsole() {
        isLogVisible = false;
        const consoleEl = document.getElementById('log-console');
        consoleEl.classList.add('translate-y-full', 'opacity-0');
        setTimeout(() => consoleEl.classList.add('hidden'), 300);
    }
    function addLog(message, type = 'info') {
        const contentEl = document.getElementById('log-content');
        const badge = document.getElementById('log-status-badge');
        let colorClass = "text-slate-300", icon = "";
        if (type === 'success') { colorClass = "text-emerald-400"; icon = "✅ "; }
        else if (type === 'error') { colorClass = "text-rose-400"; icon = "❌ "; }
        else if (type === 'warning') { colorClass = "text-amber-400"; icon = "⚠️ "; }
        else if (type === 'processing') { colorClass = "text-indigo-400"; icon = "⏳ "; }
        if (type === 'processing') { badge.className = "text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse"; badge.innerText = "Đang chạy..."; }
        else if (type === 'success') { badge.className = "text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"; badge.innerText = "Hoàn tất"; }
        else if (type === 'error') { badge.className = "text-[9px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30"; badge.innerText = "Có lỗi"; }
        else if (type === 'warning') { badge.className = "text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30"; badge.innerText = "Cảnh báo"; }
        const time = new Date().toLocaleTimeString('vi-VN');
        const div = document.createElement('div');
        div.className = `flex gap-1.5 ${colorClass}`;
        div.innerHTML = `<span class="text-slate-500 shrink-0">[${time}]</span> <span class="break-all">${icon}${message}</span>`;
        contentEl.appendChild(div);
        if (!isLogMinimized) contentEl.scrollTop = contentEl.scrollHeight;
        if (contentEl.children.length > 100) contentEl.removeChild(contentEl.firstChild);
    }
    function clearLog(e) {
        if (e) e.stopPropagation();
        document.getElementById('log-content').innerHTML = '';
        const badge = document.getElementById('log-status-badge');
        badge.className = "text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400";
        badge.innerText = "Chờ"; updateProgress(0, 1);
    }
    function updateProgress(current, total) {
        const bar = document.getElementById('log-progress-bar');
        if (!bar) return;
        if (total === 0) { bar.style.width = '0%'; return; }
        const percent = Math.min(100, Math.round((current / total) * 100));
        bar.style.width = `${percent}%`;
        bar.className = percent === 100 ? "bg-emerald-500 h-1 transition-all duration-300" : "bg-indigo-500 h-1 transition-all duration-300 animate-pulse";
    }
    """

HTML_SHELL_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Pro Quant Screener & Investment Simulator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-firestore-compat.js"></script>
    <script src="./lightweight-charts.js"></script>
    <style>
__CSS__
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans pb-10">

__BODY__

<script>
__JS__
</script>

</body>
</html>
"""

def build_html_shell(css, body, js):
    return HTML_SHELL_TEMPLATE.replace("__CSS__", css).replace("__BODY__", body).replace("__JS__", js)
