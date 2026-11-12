# -*- coding: utf-8 -*-
"""giaodien_admin.py — Module build giao diện Super Admin Panel."""

import json

def build_admin_html(price_api_url, firebase_config, super_admins_list):
    """Tạo toàn bộ nội dung file admin.html"""
    
    firebase_json = json.dumps(firebase_config, ensure_ascii=False)
    super_admins_json = json.dumps(super_admins_list, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Super Admin - Quant Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore-compat.js"></script>
    <style>
        body {{ background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .spinner {{ animation: spin 1s linear infinite; }}
        @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: #1e293b; }}
        ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #64748b; }}
        .btn-disabled {{ opacity: 0.5; cursor: not-allowed; pointer-events: none; }}
    </style>
</head>
<body class="p-4 md:p-8 min-h-screen">

    <!-- Header -->
    <div class="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
        <div>
            <h1 class="text-2xl font-black text-emerald-400"><i class="fa-solid fa-shield-halved mr-2"></i>HỆ THỐNG QUẢN TRỊ</h1>
            <p class="text-sm text-slate-400 mt-1" id="admin-email">Đang kiểm tra quyền...</p>
        </div>
        <div class="flex gap-3">
            <button onclick="logout()" class="px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-lg text-sm font-bold transition">
                <i class="fa-solid fa-right-from-bracket mr-1"></i> Đăng xuất
            </button>
            <a href="index.html" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-bold transition">
                <i class="fa-solid fa-arrow-left mr-1"></i> Về Trang Chủ
            </a>
        </div>
    </div>

    <!-- Bảng điều khiển chính -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        
        <!-- Cột 1: Cấu hình API -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h2 class="text-lg font-bold text-amber-400 mb-4"><i class="fa-solid fa-key mr-2"></i>Cấu hình API Key FHSC</h2>
            <p class="text-xs text-slate-400 mb-4">API Key của FHSC chỉ có hạn 30 ngày. Nhập key mới vào đây để Server lấy BCTC.</p>
            <div class="flex gap-2">
                <input type="password" id="fhsc-key-input" placeholder="Nhập FHSC API Key mới..." class="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-amber-500">
                <button onclick="saveFhscKey()" class="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm font-bold transition">
                    <i class="fa-solid fa-floppy-disk mr-1"></i> Lưu Key
                </button>
            </div>
            <div id="key-msg" class="mt-2 text-xs font-bold hidden"></div>
        </div>

        <!-- Cột 2: Trạng thái Server -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h2 class="text-lg font-bold text-blue-400 mb-4"><i class="fa-solid fa-server mr-2"></i>Trạng thái Server API</h2>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between"><span class="text-slate-400">URL API:</span> <span class="font-mono text-emerald-300">{price_api_url}</span></div>
                <div class="flex justify-between"><span class="text-slate-400">Trạng thái:</span> <span id="crawl-status" class="font-bold">Đang kiểm tra...</span></div>
            </div>
            <button onclick="checkStatus()" class="mt-4 w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-bold transition">
                <i class="fa-solid fa-rotate mr-1"></i> Làm mới trạng thái
            </button>
        </div>

        <!-- Cột 3: Cào dữ liệu chung -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg md:col-span-2">
            <h2 class="text-lg font-bold text-purple-400 mb-4"><i class="fa-solid fa-download mr-2"></i>Cào Dữ Liệu Hàng Loạt</h2>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
                <button onclick="callApi('/api/force-history')" id="btn-history" class="action-btn p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-chart-line text-emerald-400 text-xl"></i> Cào Nến 30 Ngày
                </button>
                <button onclick="callApi('/api/crawl-full-history')" id="btn-full-history" class="action-btn p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-clock-rotate-left text-emerald-400 text-xl"></i> Cào Full 10 Năm Nến
                </button>
                <button onclick="callApi('/api/force-bctc?limit=15')" id="btn-bctc-batch" class="action-btn p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-file-invoice-dollar text-amber-400 text-xl"></i> Cào BCTC (Nhóm 15)
                </button>
                <button onclick="callApi('/api/crawl-full-bctc')" id="btn-full-bctc" class="action-btn p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-database text-amber-400 text-xl"></i> Cào Full BCTC
                </button>
                <button onclick="callApi('/api/crawl-ratios')" id="btn-ratios" class="action-btn p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-percent text-cyan-400 text-xl"></i> Cào Chỉ Số (P/E, ROE)
                </button>
            </div>
        </div>

        <!-- Cột 4: Chấm điểm & AI -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg md:col-span-2">
            <h2 class="text-lg font-bold text-rose-400 mb-4"><i class="fa-solid fa-brain mr-2"></i>Chấm điểm & Phân tích AI</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <button onclick="callApi('/api/force-screener')" id="btn-screener" class="action-btn p-4 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-bold transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-calculator"></i> Chấm điểm lại toàn bộ (Screener)
                </button>
                <div class="flex gap-2">
                    <input type="text" id="ai-symbol-input" placeholder="Nhập mã để test AI..." class="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-fuchsia-500 uppercase">
                    <button onclick="runAI()" id="btn-ai" class="action-btn px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-500 rounded-lg text-sm font-bold transition whitespace-nowrap">
                        <i class="fa-solid fa-robot mr-1"></i> Chạy AI
                    </button>
                </div>
            </div>
            
            <!-- Nút điều khiển Cào Real-time -->
            <div class="grid grid-cols-2 gap-3 pt-3 border-t border-slate-700">
                <button onclick="callApi('/api/pause-crawl')" id="btn-pause" class="action-btn p-3 bg-red-900 hover:bg-red-800 border border-red-600 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-pause text-red-400"></i> Tạm Dừng Cào Tự Động
                </button>
                <button onclick="callApi('/api/resume-crawl')" id="btn-resume" class="action-btn p-3 bg-green-900 hover:bg-green-800 border border-green-600 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-play text-green-400"></i> Tiếp Tục Cào Tự Động
                </button>
            </div>
        </div>
    </div>

    <!-- BẢNG DANH SÁCH MÃ VÀ TRẠNG THÁI BCTC -->
    <div class="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden flex flex-col">
        
        <!-- Thanh công cụ (Search & Filter) -->
        <div class="p-4 border-b border-slate-700 flex flex-wrap justify-between items-center gap-4 bg-slate-800/80">
            <div>
                <h2 class="text-lg font-bold text-emerald-400"><i class="fa-solid fa-list-check mr-2"></i>Danh sách mã & Trạng thái BCTC</h2>
                <p class="text-xs text-slate-400 mt-1">Tick chọn các mã bên dưới để cào BCTC riêng lẻ.</p>
            </div>
            <div class="flex flex-wrap items-center gap-3">
                <!-- Ô tìm kiếm -->
                <div class="relative">
                    <i class="fa-solid fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400"></i>
                    <input type="text" id="search-bctc-input" oninput="filterBctcTable()" placeholder="Tìm mã..." class="bg-slate-900 border border-slate-600 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-emerald-500">
                </div>
                <button onclick="selectMissingBctc()" class="px-3 py-2 bg-rose-600/80 hover:bg-rose-600 rounded text-xs font-bold transition shadow-lg shadow-rose-900/50">
                    <i class="fa-solid fa-filter-circle-xmark mr-1"></i> Chọn mã chưa cào
                </button>
                <button onclick="crawlSelectedBctc()" id="btn-crawl-bctc" class="action-btn px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm font-bold transition shadow-lg shadow-amber-900/50">
                    <i class="fa-solid fa-file-import mr-1"></i> Cào BCTC Đã Chọn
                </button>
            </div>
        </div>
        
        <!-- Bảng dữ liệu -->
        <div class="overflow-x-auto max-h-[600px]">
            <table class="w-full text-left text-sm whitespace-nowrap">
                <thead class="bg-slate-900 sticky top-0 z-10 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
                    <tr>
                        <th class="px-4 py-3 text-center w-12"><input type="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()" class="w-4 h-4 cursor-pointer"></th>
                        <th class="px-4 py-3">Mã CK</th>
                        <th class="px-4 py-3">Trạng thái</th>
                        <th class="px-4 py-3">Kỳ BCTC Mới Nhất</th>
                        <th class="px-4 py-3">Cập nhật lúc</th>
                        <th class="px-4 py-3 text-center">Hành động</th>
                    </tr>
                </thead>
                <tbody id="bctc-table-body" class="divide-y divide-slate-700/50">
                    <tr><td colspan="6" class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner spinner mr-2"></i> Đang tải danh sách...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Bảng Log (Console) -->
    <div class="mt-8 bg-black rounded-xl border border-slate-700 p-4 h-64 overflow-y-auto font-mono text-xs" id="console-log">
        <div class="text-slate-500">// Hệ thống log sẽ hiển thị ở đây...</div>
    </div>

    <script>
        // ══════════════════════════════════════════════════
        // CONFIG
        // ══════════════════════════════════════════════════
        const PRICE_API_URL = "{price_api_url}";
        const firebaseConfig = {firebase_json};
        const SUPER_ADMINS = {super_admins_json};
        
        if (!firebase.apps.length) {{
            firebase.initializeApp(firebaseConfig);
        }}
        const auth = firebase.auth();
        const db = firebase.firestore();

        let currentDataList = []; 
        let filteredDataList = []; 
        let isServerBusy = false; 
        let isPaused = false;

        // ══════════════════════════════════════════════════
        // HÀM LOG RA CONSOLE
        // ══════════════════════════════════════════════════
        function log(msg, type = 'info') {{
            const consoleEl = document.getElementById('console-log');
            const time = new Date().toLocaleTimeString('vi-VN');
            let color = 'text-slate-300';
            if (type === 'error') color = 'text-rose-400';
            if (type === 'success') color = 'text-emerald-400';
            if (type === 'warning') color = 'text-amber-400';
            
            const line = document.createElement('div');
            line.className = color;
            line.innerText = `[${{time}}] ${{msg}}`;
            consoleEl.appendChild(line);
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }}

        // ══════════════════════════════════════════════════
        // AUTH HOOKS
        // ══════════════════════════════════════════════════
        auth.onAuthStateChanged(async (user) => {{
            if (!user) {{
                alert("Vui lòng đăng nhập để vào trang Admin!");
                window.location.href = "index.html";
                return;
            }}
            
            document.getElementById('admin-email').innerText = `Xin chào, ${{user.email}}`;
            
            if (SUPER_ADMINS.includes(user.email.toLowerCase())) {{
                log("Đăng nhập thành công với quyền Super Admin.", "success");
                checkStatus();
                loadSavedKey();
                loadBctcStatus(); 
                setInterval(checkStatus, 10000);
                return;
            }}

            try {{
                const doc = await db.collection('allowed_users').doc(user.email.toLowerCase()).get();
                if (doc.exists && doc.data().role === 'admin') {{
                    log("Đăng nhập thành công với quyền Admin (Firestore).", "success");
                    checkStatus();
                    loadSavedKey();
                    loadBctcStatus(); 
                    setInterval(checkStatus, 10000);
                }} else {{
                    document.body.innerHTML = `<div class="flex h-screen items-center justify-center text-rose-500 text-2xl font-bold"><i class="fa-solid fa-ban mr-2"></i> TRUY CẬP BỊ TỪ CHỐI</div>`;
                }}
            }} catch (e) {{
                log("Lỗi kiểm tra quyền: " + e.message, "error");
            }}
        }});

        function logout() {{
            auth.signOut().then(() => window.location.href = "index.html");
        }}

        // ══════════════════════════════════════════════════
        // LOAD DANH SÁCH BCTC
        // ══════════════════════════════════════════════════
        async function loadBctcStatus() {{
            const tbody = document.getElementById('bctc-table-body');
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner spinner mr-2"></i> Đang tải danh sách...</td></tr>`;
            
            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/bctc-status?t=` + new Date().getTime());
                const json = await res.json();
                
                if (json.status === 'success') {{
                    currentDataList = json.data;
                    filterBctcTable();
                    log(`Đã tải danh sách BCTC của ${{currentDataList.length}} mã.`, "success");
                }} else {{
                    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-rose-500">Lỗi tải dữ liệu: ${{json.message}}</td></tr>`;
                }}
            }} catch (e) {{
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-rose-500">Lỗi kết nối Server API.</td></tr>`;
                log(`Lỗi tải BCTC: ${{e.message}}`, "error");
            }}
        }}

        function filterBctcTable() {{
            const keyword = document.getElementById('search-bctc-input').value.trim().toUpperCase();
            if (!keyword) {{
                filteredDataList = [...currentDataList];
            }} else {{
                filteredDataList = currentDataList.filter(item => item.symbol.includes(keyword));
            }}
            renderBctcTable();
        }}

        function renderBctcTable() {{
            const tbody = document.getElementById('bctc-table-body');
            tbody.innerHTML = '';
            
            if (filteredDataList.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-500">Không có mã nào phù hợp.</td></tr>`;
                return;
            }}

            filteredDataList.forEach((item, index) => {{
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-700/30 transition';
                
                let badgeHtml = '';
                if (item.has_bctc) {{
                    let isOld = false;
                    try {{
                        const parts = item.updated_at.split(' ')[0].split('/');
                        const updateDate = new Date(parts[2], parts[1] - 1, parts[0]);
                        const diffDays = (new Date() - updateDate) / (1000 * 60 * 60 * 24);
                        if (diffDays > 45) isOld = true;
                    }} catch(e) {{}}

                    if (isOld) {{
                        badgeHtml = `<span class="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-1 rounded text-[10px] font-bold">Cũ (>45 ngày)</span>`;
                    }} else {{
                        badgeHtml = `<span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded text-[10px] font-bold">Đã có</span>`;
                    }}
                }} else {{
                    badgeHtml = `<span class="bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-1 rounded text-[10px] font-bold">Chưa cào</span>`;
                }}

                tr.innerHTML = `
                    <td class="px-4 py-2 text-center">
                        <input type="checkbox" class="bctc-checkbox w-4 h-4 cursor-pointer" data-symbol="${{item.symbol}}" data-has-bctc="${{item.has_bctc}}" onchange="updateSelectedCount()">
                    </td>
                    <td class="px-4 py-2 font-bold text-white">${{item.symbol}}</td>
                    <td class="px-4 py-2">${{badgeHtml}}</td>
                    <td class="px-4 py-2 text-slate-300 font-mono">${{item.latest_period}}</td>
                    <td class="px-4 py-2 text-slate-400 text-xs">${{item.updated_at}}</td>
                    <td class="px-4 py-2 text-center">
                        <button onclick="crawlSingleBctc('${{item.symbol}}')" class="px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs transition" title="Cào lại mã này">
                            <i class="fa-solid fa-rotate-right"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function toggleSelectAll() {{
            const mainCheckbox = document.getElementById('selectAllCheckbox');
            const isChecked = mainCheckbox.checked;
            const checkboxes = document.querySelectorAll('.bctc-checkbox');
            checkboxes.forEach(cb => cb.checked = !isChecked);
            mainCheckbox.checked = !isChecked;
            updateSelectedCount();
        }}

        function selectMissingBctc() {{
            const checkboxes = document.querySelectorAll('.bctc-checkbox');
            checkboxes.forEach(cb => {{
                if (cb.getAttribute('data-has-bctc') === 'false') {{
                    cb.checked = true;
                }} else {{
                    cb.checked = false;
                }}
            }});
            document.getElementById('selectAllCheckbox').checked = false;
            updateSelectedCount();
        }}

        function updateSelectedCount() {{
            const checked = document.querySelectorAll('.bctc-checkbox:checked');
            const btn = document.getElementById('btn-crawl-bctc');
            if (checked.length > 0) {{
                btn.innerHTML = `<i class="fa-solid fa-file-import mr-1"></i> Cào ${{checked.length}} mã đã chọn`;
            }} else {{
                btn.innerHTML = `<i class="fa-solid fa-file-import mr-1"></i> Cào BCTC Đã Chọn`;
            }}
        }}

        // ══════════════════════════════════════════════════
        // CÀO BCTC (CHỌN LỌC)
        // ══════════════════════════════════════════════════
        async function crawlSelectedBctc() {{
            if (isServerBusy) {{
                alert("Server đang bận xử lý tiến trình khác, vui lòng đợi!");
                return;
            }}

            const checked = document.querySelectorAll('.bctc-checkbox:checked');
            if (checked.length === 0) {{
                alert("Vui lòng tick chọn ít nhất 1 mã!");
                return;
            }}
            
            const symbols = Array.from(checked).map(cb => cb.dataset.symbol).join(',');
            
            if (!confirm(`Bạn có chắc muốn cào BCTC cho ${{checked.length}} mã đã chọn?\\nDanh sách: ${{symbols}}`)) return;
            
            log(`Đang kích hoạt cào BCTC cho ${{checked.length}} mã...`, "warning");
            toggleAllButtons(false, "Đang xử lý...");

            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/force-bctc?symbols=${{symbols}}`);
                const data = await res.json();
                if (data.status === 'success') {{
                    log(`✅ ${{data.message}}`, "success");
                    setTimeout(() => {{
                        loadBctcStatus();
                        checkStatus();
                    }}, 5000);
                }} else {{
                    log(`❌ Lỗi từ Server: ${{data.message}}`, "error");
                    toggleAllButtons(true);
                }}
            }} catch (e) {{
                log(`❌ Lỗi kết nối mạng: ${{e.message}}`, "error");
                toggleAllButtons(true);
            }}
        }}

        async function crawlSingleBctc(symbol) {{
            if (isServerBusy) {{
                alert("Server đang bận xử lý tiến trình khác, vui lòng đợi!");
                return;
            }}
            if (!confirm(`Bạn có chắc muốn cào lại BCTC cho mã ${{symbol}}?`)) return;
            
            log(`Đang kích hoạt cào BCTC cho ${{symbol}}...`, "warning");
            toggleAllButtons(false, "Đang xử lý...");
            
            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/force-bctc?symbols=${{symbol}}`);
                const data = await res.json();
                if (data.status === 'success') {{
                    log(`✅ ${{data.message}}`, "success");
                    setTimeout(() => {{
                        loadBctcStatus();
                        checkStatus();
                    }}, 5000);
                }} else {{
                    log(`❌ Lỗi từ Server: ${{data.message}}`, "error");
                    toggleAllButtons(true);
                }}
            }} catch (e) {{
                log(`❌ Lỗi kết nối mạng: ${{e.message}}`, "error");
                toggleAllButtons(true);
            }}
        }}

        // Hàm bật/tắt TẤT CẢ các nút thao tác (trừ nút checkStatus)
        function toggleAllButtons(enable, text = null) {{
            const btns = document.querySelectorAll('.action-btn');
            btns.forEach(btn => {{
                if (enable) {{
                    btn.classList.remove('btn-disabled');
                    // Khôi phục text ban đầu (cần lưu text gốc)
                    if (btn.id === 'btn-crawl-bctc') updateSelectedCount();
                    else if (btn.id === 'btn-screener') btn.innerHTML = '<i class="fa-solid fa-calculator"></i> Chấm điểm lại toàn bộ (Screener)';
                    else if (btn.id === 'btn-ai') btn.innerHTML = '<i class="fa-solid fa-robot mr-1"></i> Chạy AI';
                    else if (btn.id === 'btn-history') btn.innerHTML = '<i class="fa-solid fa-chart-line text-emerald-400 text-xl"></i> Cào Nến 30 Ngày';
                    else if (btn.id === 'btn-full-history') btn.innerHTML = '<i class="fa-solid fa-clock-rotate-left text-emerald-400 text-xl"></i> Cào Full 10 Năm Nến';
                    else if (btn.id === 'btn-bctc-batch') btn.innerHTML = '<i class="fa-solid fa-file-invoice-dollar text-amber-400 text-xl"></i> Cào BCTC (Nhóm 15)';
                    else if (btn.id === 'btn-full-bctc') btn.innerHTML = '<i class="fa-solid fa-database text-amber-400 text-xl"></i> Cào Full BCTC';
                    else if (btn.id === 'btn-ratios') btn.innerHTML = '<i class="fa-solid fa-percent text-cyan-400 text-xl"></i> Cào Chỉ Số (P/E, ROE)';
                    else if (btn.id === 'btn-pause') btn.innerHTML = '<i class="fa-solid fa-pause text-red-400"></i> Tạm Dừng Cào Tự Động';
                    else if (btn.id === 'btn-resume') btn.innerHTML = '<i class="fa-solid fa-play text-green-400"></i> Tiếp Tục Cào Tự Động';
                }} else {{
                    btn.classList.add('btn-disabled');
                    if (btn.id === 'btn-crawl-bctc') btn.innerHTML = `<i class="fa-solid fa-spinner spinner mr-1"></i> ${{text || 'Đang xử lý...'}}`;
                }}
            }});
        }}

        // ══════════════════════════════════════════════════
        // CÁC HÀM GỌI API CHUNG
        // ══════════════════════════════════════════════════
        async function checkStatus() {{
            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/status`);
                const data = await res.json();
                const el = document.getElementById('crawl-status');
                
                isPaused = data.is_paused || false;

                if (data.is_crawling) {{
                    el.innerText = "ĐANG XỬ LÝ (BẬN)";
                    el.className = "font-bold text-amber-400 animate-pulse";
                    isServerBusy = true;
                    toggleAllButtons(false, "Server đang bận...");
                }} else if (isPaused) {{
                    el.innerText = "ĐANG TẠM DỪNG";
                    el.className = "font-bold text-rose-400";
                    isServerBusy = false;
                    toggleAllButtons(true);
                }} else {{
                    el.innerText = "SẴN SÀNG";
                    el.className = "font-bold text-emerald-400";
                    isServerBusy = false;
                    toggleAllButtons(true);
                }}
            }} catch (e) {{
                document.getElementById('crawl-status').innerText = "MẤT KẾT NỐI";
                document.getElementById('crawl-status').className = "font-bold text-rose-500";
                log("Không thể kết nối đến Server API.", "error");
            }}
        }}

        async function callApi(endpoint) {{
            if (isServerBusy) {{
                alert("Server đang bận xử lý tiến trình khác, vui lòng đợi!");
                return;
            }}
            
            log(`Đang gửi yêu cầu tới: ${{endpoint}}...`, "warning");
            toggleAllButtons(false, "Đang chạy...");
            
            try {{
                const res = await fetch(`${{PRICE_API_URL}}${{endpoint}}`);
                const data = await res.json();
                if (data.status === 'success') {{
                    log(`✅ Thành công: ${{data.message}}`, "success");
                    // Tự động bật lại nút sau 2 giây nếu là lệnh chạy nhanh
                    setTimeout(() => {{
                        checkStatus();
                        if (endpoint.includes('bctc')) loadBctcStatus();
                    }}, 2000);
                }} else {{
                    log(`❌ Lỗi từ Server: ${{data.message}}`, "error");
                    toggleAllButtons(true); // Mở khóa nếu lỗi ngay
                }}
            }} catch (e) {{
                log(`❌ Lỗi kết nối mạng: ${{e.message}}`, "error");
                toggleAllButtons(true);
            }}
        }}

        async function runAI() {{
            if (isServerBusy) {{
                alert("Server đang bận xử lý tiến trình khác, vui lòng đợi!");
                return;
            }}
            
            const symbol = document.getElementById('ai-symbol-input').value.trim().toUpperCase();
            if (!symbol) {{ alert("Vui lòng nhập mã cổ phiếu!"); return; }}
            
            log(`Đang gọi AI phân tích mã ${{symbol}} (Có thể mất 10-20s)...`, "warning");
            toggleAllButtons(false, "AI đang chạy...");
            
            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/ai-analyze?symbol=${{symbol}}`);
                const data = await res.json();
                if (data.status === 'success') {{
                    log(`✅ AI đã phân tích xong ${{symbol}}!`, "success");
                    log(`=> Khuyến nghị: ${{data.data.recommendation}}`, "success");
                    log(`=> Nhận định: ${{data.data.bctc}}`, "info");
                }} else {{
                    log(`❌ Lỗi AI: ${{data.message}}`, "error");
                }}
            }} catch (e) {{
                log(`❌ Lỗi kết nối: ${{e.message}}`, "error");
            }} finally {{
                toggleAllButtons(true);
            }}
        }}

        // ══════════════════════════════════════════════════
        // NHẬP API KEY FHSC
        // ══════════════════════════════════════════════════
        async function saveFhscKey() {{
            const key = document.getElementById('fhsc-key-input').value.trim();
            if (!key) {{ alert("Vui lòng nhập Key!"); return; }}
            
            const msgEl = document.getElementById('key-msg');
            msgEl.classList.remove('hidden', 'text-emerald-400', 'text-rose-400');
            msgEl.innerText = "Đang lưu...";
            
            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/set-fhsc-key`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key }})
                }});
                const data = await res.json();
                if (data.status === 'success') {{
                    msgEl.innerText = "✅ Lưu thành công!";
                    msgEl.classList.add('text-emerald-400');
                    log("Đã cập nhật FHSC API Key mới vào Database.", "success");
                    localStorage.setItem("saved_fhsc_key", key);
                }} else {{
                    msgEl.innerText = "❌ " + data.message;
                    msgEl.classList.add('text-rose-400');
                }}
            }} catch (e) {{
                msgEl.innerText = "❌ Lỗi kết nối Server";
                msgEl.classList.add('text-rose-400');
            }}
        }}

        function loadSavedKey() {{
            const saved = localStorage.getItem("saved_fhsc_key");
            if (saved) {{
                document.getElementById('fhsc-key-input').value = saved;
            }}
        }}
    </script>
</body>
</html>"""
    return html_content
