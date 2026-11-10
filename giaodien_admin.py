# -*- coding: utf-8 -*-
"""giaodien_admin.py — Modal admin panel & User Profile."""

def build_admin_modal_html():
    return r"""
    <!-- MODAL CHUNG: USER PROFILE + ADMIN PANEL -->
    <div id="admin-modal" class="fixed inset-0 z-[9999999] flex items-center justify-center bg-black/80 backdrop-blur-sm hidden p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90dvh]">
            
            <!-- HEADER MODAL -->
            <div class="bg-slate-950 px-5 py-4 border-b border-slate-800 flex justify-between items-center">
                <div class="flex items-center space-x-2">
                    <i class="fa-solid fa-circle-user text-emerald-400 text-lg"></i>
                    <h3 class="text-sm font-bold text-white" id="modalTitle">Tài khoản của tôi</h3>
                </div>
                <button type="button" onclick="closeAdminModal()" class="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <!-- PHẦN THÔNG TIN USER -->
            <div class="p-5 bg-slate-800/50 border-b border-slate-700 flex flex-col sm:flex-row justify-between items-center gap-4">
                <div>
                    <div class="text-[11px] text-slate-400 mb-1 uppercase tracking-wider font-semibold">Email đăng nhập</div>
                    <div class="text-sm font-bold text-white" id="modalUserEmail">---</div>
                    <div class="text-xs text-slate-400 mt-2">
                        <i class="fa-solid fa-clock text-emerald-500"></i> Hạn sử dụng: 
                        <span class="text-emerald-400 font-bold" id="modalExpireDate">Đang tải...</span>
                    </div>
                </div>
                <button onclick="openUserRenewalModal()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-emerald-900/50">
                    <i class="fa-solid fa-plus-circle"></i> Gia hạn tài khoản
                </button>
            </div>

            <!-- TAB SWITCHER (Chỉ hiện nếu là Admin) -->
            <div id="adminTabsWrapper" class="flex border-b border-slate-800 bg-slate-950 px-5 gap-4 hidden">
                <button onclick="switchAdminTab('users')" id="tabBtnUsers" class="py-3 text-xs font-bold text-emerald-400 border-b-2 border-emerald-400 transition">Quản lý Người dùng</button>
                <button onclick="switchAdminTab('renewals')" id="tabBtnRenewals" class="py-3 text-xs font-bold text-slate-400 border-b-2 border-transparent transition">Duyệt Gia hạn (<span id="pendingCount">0</span>)</button>
            </div>

            <!-- NỘI DUNG TAB (Chỉ hiện nếu là Admin) -->
            <div id="adminTabsContent" class="p-5 overflow-y-auto space-y-4 flex-grow hidden">
                <!-- TAB 1: USERS -->
                <div id="adminTabUsers" class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                          <tr class="border-b border-slate-800 text-slate-400 bg-slate-950">
                           <th class="p-3">Email</th>
                           <th class="p-3">Hạn sử dụng</th>
                           <th class="p-3">Quyền</th>
                          </tr>
                         </thead>
                        <tbody id="admin-users-list" class="divide-y divide-slate-800">
                            <tr><td colspan="3" class="p-4 text-center text-slate-500">Đang tải danh sách...</td></tr>
                        </tbody>
                    </table>
                </div>

                <!-- TAB 2: RENEWALS -->
                <div id="adminTabRenewals" class="overflow-x-auto hidden">
                    <table class="w-full text-left text-xs">
                        <thead>
                          <tr class="border-b border-slate-800 text-slate-400 bg-slate-950">
                           <th class="p-3">Email</th>
                           <th class="p-3">Gói / Số tiền</th>
                           <th class="p-3">Mã CK</th>
                           <th class="p-3">Thao tác</th>
                          </tr>
                         </thead>
                        <tbody id="admin-renewals-list" class="divide-y divide-slate-800">
                            <tr><td colspan="4" class="p-4 text-center text-slate-500">Đang tải yêu cầu...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- FOOTER MODAL -->
            <div class="bg-slate-950 px-5 py-3 border-t border-slate-800 flex justify-between items-center mt-auto">
                <button type="button" onclick="triggerSignOut()" class="px-3 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition">
                    <i class="fa-solid fa-right-from-bracket"></i> Đăng xuất
                </button>
                <button type="button" onclick="closeAdminModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold">Đóng</button>
            </div>
        </div>
    </div>
    """

def build_admin_js():
    return r"""
    // ══════════════════════════════════════════════════
    // ADMIN PANEL & USER PROFILE JS
    // ══════════════════════════════════════════════════

    function switchAdminTab(tab) {
        const usersTab = document.getElementById('adminTabUsers');
        const renewalsTab = document.getElementById('adminTabRenewals');
        const btnUsers = document.getElementById('tabBtnUsers');
        const btnRenewals = document.getElementById('tabBtnRenewals');

        if (tab === 'users') {
            usersTab.classList.remove('hidden');
            renewalsTab.classList.add('hidden');
            btnUsers.className = "py-3 text-xs font-bold text-emerald-400 border-b-2 border-emerald-400 transition";
            btnRenewals.className = "py-3 text-xs font-bold text-slate-400 border-b-2 border-transparent transition";
            loadAdminUsers();
        } else {
            usersTab.classList.add('hidden');
            renewalsTab.classList.remove('hidden');
            btnRenewals.className = "py-3 text-xs font-bold text-emerald-400 border-b-2 border-emerald-400 transition";
            btnUsers.className = "py-3 text-xs font-bold text-slate-400 border-b-2 border-transparent transition";
            loadAdminRenewals();
        }
    }

    // Hàm mở modal chung
    async function openAdminModal() {
        if (!window.auth || !window.auth.currentUser) return;
        
        document.getElementById('admin-modal').classList.remove('hidden');
        
        // 1. Điền thông tin User
        const email = window.auth.currentUser.email;
        document.getElementById('modalUserEmail').innerText = email;
        
        const expText = document.getElementById('hiddenExpireDate');
        document.getElementById('modalExpireDate').innerText = expText ? expText.innerText : 'Đang tải...';

        // Lấy thẻ chứa nút Gia hạn (nằm cạnh thông tin email)
        const renewBtn = document.querySelector('button[onclick="openUserRenewalModal()"]');

        // 2. Kiểm tra quyền Admin để hiện Tabs
        try {
            if (!window.db) return;
            const doc = await window.db.collection('allowed_users').doc(email.toLowerCase()).get();
            const isAdmin = doc.exists && doc.data().role === 'admin';
            
            const tabsWrapper = document.getElementById('adminTabsWrapper');
            const tabsContent = document.getElementById('adminTabsContent');
            
            if (isAdmin) {
                tabsWrapper.classList.remove('hidden');
                tabsContent.classList.remove('hidden');
                document.getElementById('modalTitle').innerText = "Quản Trị Hệ Thống (Admin)";
                
                // ẨN NÚT GIA HẠN VỚI ADMIN VÀ ĐỔI TEXT HẠN DÙNG
                if (renewBtn) renewBtn.style.display = 'none';
                document.getElementById('modalExpireDate').innerText = "Vô hạn (Admin)";
                
                switchAdminTab('users'); // Load tab users mặc định
            } else {
                tabsWrapper.classList.add('hidden');
                tabsContent.classList.add('hidden');
                document.getElementById('modalTitle').innerText = "Tài khoản của tôi";
                
                // HIỆN LẠI NÚT GIA HẠN VỚI USER
                if (renewBtn) renewBtn.style.display = 'flex';
            }
        } catch (e) {
            console.warn("Không thể check quyền admin", e);
        }
    }

    function closeAdminModal() {
        document.getElementById('admin-modal').classList.add('hidden');
    }

    // Hàm escape HTML chống XSS
    function escapeHTML(str) {
        if (!str) return '';
        return String(str).replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    async function loadAdminUsers() {
        const listEl = document.getElementById('admin-users-list');
        listEl.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-slate-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Đang tải danh sách...</td></tr>`;

        try {
            const snapshot = await window.db.collection('allowed_users').get();
            listEl.innerHTML = '';
            if (snapshot.empty) {
                listEl.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-slate-400">Chưa có người dùng nào.</td></tr>`;
                return;
            }

            // 1. Chuyển dữ liệu thành mảng để dễ sắp xếp
            let users = [];
            snapshot.forEach(doc => {
                let data = doc.data();
                data.id = doc.id;
                users.push(data);
            });

            // 2. Sắp xếp: Ai có hạn sử dụng xa nhất (lớn nhất) thì lên đầu
            users.sort((a, b) => {
                let dateA = a.expiresAt ? new Date(a.expiresAt).getTime() : 0;
                let dateB = b.expiresAt ? new Date(b.expiresAt).getTime() : 0;
                return dateB - dateA; // Giảm dần
            });

            // 3. Render ra bảng
            users.forEach(data => {
                let dateStr = '—';
                if (data.expiresAt) {
                    let d = new Date(data.expiresAt);
                    // Kiểm tra nếu ngày hợp lệ thì mới format
                    if (!isNaN(d.getTime())) {
                        dateStr = d.toLocaleDateString('vi-VN');
                    } else {
                        dateStr = '<span class="text-rose-400 text-[10px]">Lỗi data</span>';
                    }
                }

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/50 transition";
                
                // Áp dụng escapeHTML chống XSS
                const safeEmail = escapeHTML(data.email || data.id);
                const role = data.role || 'user';
                
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-white">${safeEmail}</td>
                    <td class="p-3 text-slate-300">${dateStr}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${role === 'admin' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-300'}">${role}</span></td>
                `;
                listEl.appendChild(tr);
            });
        } catch (err) {
            listEl.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-rose-400">Không có quyền truy cập.</td></tr>`;
        }
    }

    async function loadAdminRenewals() {
        const listEl = document.getElementById('admin-renewals-list');
        listEl.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-slate-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Đang tải yêu cầu...</td></tr>`;

        try {
            const snapshot = await window.db.collection('renewal_requests').where('status', '==', 'pending').get();
            document.getElementById('pendingCount').innerText = snapshot.size;
            listEl.innerHTML = '';
            if (snapshot.empty) {
                listEl.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-slate-400">Không có yêu cầu gia hạn nào đang chờ.</td></tr>`;
                return;
            }
            snapshot.forEach(doc => {
                const data = doc.data();
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/50 transition";
                // Áp dụng escapeHTML chống XSS
                const safeEmail = escapeHTML(data.email);
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-white">${safeEmail}</td>
                    <td class="p-3 text-emerald-400 font-bold">${data.packageId} (${data.amount?.toLocaleString()}đ)</td>
                    <td class="p-3 font-mono text-amber-300">${data.code}</td>
                    <td class="p-3">
                        <button onclick="approveRenewal('${doc.id}', '${data.email}', '${data.packageId}', ${data.days || 30})" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-bold transition">Duyệt</button>
                    </td>
                `;
                listEl.appendChild(tr);
            });
        } catch (err) {
            listEl.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-rose-400">Lỗi tải danh sách gia hạn.</td></tr>`;
        }
    }

    // Sử dụng số ngày (days) truyền vào thay vì đoán qua tên gói
    async function approveRenewal(reqId, email, packageId, daysToAdd) {
        if (!confirm(`Xác nhận duyệt gia hạn cho ${email} (${packageId})?`)) return;
        try {
            const userRef = window.db.collection('allowed_users').doc(email.toLowerCase());
            const userDoc = await userRef.get();
            
            let newExp = new Date();
            if (userDoc.exists && userDoc.data().expiresAt) {
                let currentExp = new Date(userDoc.data().expiresAt);
                if (currentExp > newExp) newExp = currentExp;
            }
            newExp.setDate(newExp.getDate() + (daysToAdd || 30));

            await userRef.set({ expiresAt: newExp.toISOString() }, { merge: true });
            await window.db.collection('renewal_requests').doc(reqId).update({ status: 'approved' });

            alert('✅ Đã duyệt gia hạn thành công!');
            loadAdminRenewals();
        } catch (e) {
            alert('Lỗi duyệt: ' + e.message);
        }
    }
    """
