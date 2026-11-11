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
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #1e293b; }}
        ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #64748b; }}
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
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        
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

        <!-- Cột 3: Cào dữ liệu -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg md:col-span-2">
            <h2 class="text-lg font-bold text-purple-400 mb-4"><i class="fa-solid fa-download mr-2"></i>Cào Dữ Liệu</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button onclick="callApi('/api/force-history')" class="p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-chart-line text-emerald-400 text-xl"></i> Cào Nến 30 Ngày
                </button>
                <button onclick="callApi('/api/crawl-full-history')" class="p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-clock-rotate-left text-emerald-400 text-xl"></i> Cào Full 10 Năm Nến
                </button>
                <button onclick="callApi('/api/force-bctc?limit=15')" class="p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-file-invoice-dollar text-amber-400 text-xl"></i> Cào BCTC (Nhóm 15)
                </button>
                <button onclick="callApi('/api/crawl-full-bctc')" class="p-3 bg-slate-900 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-bold transition flex flex-col items-center gap-2">
                    <i class="fa-solid fa-database text-amber-400 text-xl"></i> Cào Full BCTC
                </button>
            </div>
        </div>

        <!-- Cột 4: Chấm điểm & AI -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg md:col-span-2">
            <h2 class="text-lg font-bold text-rose-400 mb-4"><i class="fa-solid fa-brain mr-2"></i>Chấm điểm & Phân tích AI</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button onclick="callApi('/api/force-screener')" class="p-4 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-bold transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-calculator"></i> Chấm điểm lại toàn bộ (Screener)
                </button>
                <div class="flex gap-2">
                    <input type="text" id="ai-symbol-input" placeholder="Nhập mã để test AI..." class="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-fuchsia-500 uppercase">
                    <button onclick="runAI()" class="px-4 py-2 bg-fuchsia-600 hover:bg-fuchsia-500 rounded-lg text-sm font-bold transition whitespace-nowrap">
                        <i class="fa-solid fa-robot mr-1"></i> Chạy AI
                    </button>
                </div>
            </div>
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
        // KIỂM TRA QUYỀN ADMIN
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
                return;
            }}

            try {{
                const doc = await db.collection('allowed_users').doc(user.email.toLowerCase()).get();
                if (doc.exists && doc.data().role === 'admin') {{
                    log("Đăng nhập thành công với quyền Admin (Firestore).", "success");
                    checkStatus();
                    loadSavedKey();
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
        // CÁC HÀM GỌI API SERVER
        // ══════════════════════════════════════════════════
        async function checkStatus() {{
            try {{
                const res = await fetch(`${{PRICE_API_URL}}/api/status`);
                const data = await res.json();
                const el = document.getElementById('crawl-status');
                if (data.is_crawling) {{
                    el.innerText = "ĐANG CÀO REAL-TIME";
                    el.className = "font-bold text-amber-400 animate-pulse";
                }} else {{
                    el.innerText = "SẴN SÀNG";
                    el.className = "font-bold text-emerald-400";
                }}
            }} catch (e) {{
                document.getElementById('crawl-status').innerText = "MẤT KẾT NỐI";
                document.getElementById('crawl-status').className = "font-bold text-rose-500";
                log("Không thể kết nối đến Server API.", "error");
            }}
        }}

        async function callApi(endpoint) {{
            log(`Đang gửi yêu cầu tới: ${{endpoint}}...`, "warning");
            try {{
                const res = await fetch(`${{PRICE_API_URL}}${{endpoint}}`);
                const data = await res.json();
                if (data.status === 'success') {{
                    log(`✅ Thành công: ${{data.message}}`, "success");
                    checkStatus();
                }} else {{
                    log(`❌ Lỗi từ Server: ${{data.message}}`, "error");
                }}
            }} catch (e) {{
                log(`❌ Lỗi kết nối mạng: ${{e.message}}`, "error");
            }}
        }}

        async function runAI() {{
            const symbol = document.getElementById('ai-symbol-input').value.trim().toUpperCase();
            if (!symbol) {{ alert("Vui lòng nhập mã cổ phiếu!"); return; }}
            
            log(`Đang gọi AI phân tích mã ${{symbol}} (Có thể mất 10-20s)...`, "warning");
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
