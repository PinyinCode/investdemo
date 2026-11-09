# -*- coding: utf-8 -*-
"""giaodien_admin.py — Modal admin panel."""


def build_admin_modal_html():
    return r"""
    <!-- MODAL ADMIN -->
    <div id="admin-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm hidden p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90dvh]">
            <div class="bg-slate-950 px-5 py-4 border-b border-slate-800 flex justify-between items-center">
                <div class="flex items-center space-x-2">
                    <i class="fa-solid fa-user-shield text-amber-400"></i>
                    <h3 class="text-sm font-bold text-white">Quản Trị Hệ Thống (Admin Panel)</h3>
                </div>
                <button type="button" onclick="closeAdminModal()" class="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            
            <!-- TAB SWITCHER TRONG ADMIN -->
            <div class="flex border-b border-slate-800 bg-slate-950 px-5 gap-4">
                <button onclick="switchAdminTab('users')" id="tabBtnUsers" class="py-3 text-xs font-bold text-emerald-400 border-b-2 border-emerald-400 transition">Quản lý Người dùng</button>
                <button onclick="switchAdminTab('renewals')" id="tabBtnRenewals" class="py-3 text-xs font-bold text-slate-400 border-b-2 border-transparent transition">Duyệt Gia hạn (<span id="pendingCount">0</span>)</button>
            </div>

            <div class="p-5 overflow-y-auto space-y-4 flex-grow">
                <!-- TAB 1: USER LIST -->
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

                <!-- TAB 2: RENEWAL REQUESTS -->
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

            <div class="bg-slate-950 px-5 py-3 border-t border-slate-800 flex justify-between items-center">
                <button type="button" onclick="auth.signOut()" class="px-3 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition">
                    <i class="fa-solid fa-right-from-bracket"></i> Đăng xuất tài khoản
                </button>
                <button type="button" onclick="closeAdminModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold">Đóng</button>
            </div>
        </div>
    </div>
    """


def build_admin_js():
    return r"""
    // ══════════════════════════════════════════════════
    // ADMIN PANEL & RENEWAL MANAGEMENT
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

    async function openAdminModal() {
        document.getElementById('admin-modal').classList.remove('hidden');
        switchAdminTab('users');
    }

    function closeAdminModal() {
        document.getElementById('admin-modal').classList.add('hidden');
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
            snapshot.forEach(doc => {
                const data = doc.data();
                const expDate = data.expiresAt ? new Date(data.expiresAt) : null;
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/50 transition";
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-white">${data.email || doc.id}</td>
                    <td class="p-3 text-slate-300">${expDate ? expDate.toLocaleDateString('vi-VN') : '—'}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${data.role === 'admin' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-300'}">${data.role || 'user'}</span></td>
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
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-white">${data.email}</td>
                    <td class="p-3 text-emerald-400 font-bold">${data.packageId} (${data.amount?.toLocaleString()}đ)</td>
                    <td class="p-3 font-mono text-amber-300">${data.code}</td>
                    <td class="p-3">
                        <button onclick="approveRenewal('${doc.id}', '${data.email}', '${data.packageId}')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-bold transition">Duyệt</button>
                    </td>
                `;
                listEl.appendChild(tr);
            });
        } catch (err) {
            listEl.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-rose-400">Lỗi tải danh sách gia hạn.</td></tr>`;
        }
    }

    async function approveRenewal(reqId, email, packageId) {
        if (!confirm(`Xác nhận duyệt gia hạn cho ${email} (${packageId})?`)) return;
        try {
            // 1. Tính thêm ngày hạn (Ví dụ: gói 30 ngày hoặc 90 ngày tuỳ packageId)
            let daysToAdd = 30;
            if (packageId.includes('3th')) daysToAdd = 90;
            if (packageId.includes('1nam') || packageId.includes('year')) daysToAdd = 365;

            const userRef = window.db.collection('allowed_users').doc(email.toLowerCase());
            const userDoc = await userRef.get();
            
            let newExp = new Date();
            if (userDoc.exists && userDoc.data().expiresAt) {
                let currentExp = new Date(userDoc.data().expiresAt);
                if (currentExp > newExp) newExp = currentExp; // Nếu chưa hết hạn thì cộng dồn tiếp
            }
            newExp.setDate(newExp.getDate() + daysToAdd);

            // Cập nhật hạn user
            await userRef.set({ expiresAt: newExp.toISOString() }, { merge: true });

            // Đổi trạng thái request thành approved
            await window.db.collection('renewal_requests').doc(reqId).update({ status: 'approved' });

            alert('✅ Đã duyệt gia hạn thành công!');
            loadAdminRenewals();
        } catch (e) {
            alert('Lỗi duyệt: ' + e.message);
        }
    }
    """
