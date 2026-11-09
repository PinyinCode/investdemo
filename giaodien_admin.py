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
            <div class="p-5 overflow-y-auto space-y-4 flex-grow">
                <div class="overflow-x-auto">
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
            </div>
            <div class="bg-slate-950 px-5 py-3 border-t border-slate-800 flex justify-between items-center">
                <!-- NÚT ĐĂNG XUẤT ĐẶT TRONG ADMIN PANEL -->
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
    // ADMIN PANEL
    // ══════════════════════════════════════════════════

    async function openAdminModal() {
        document.getElementById('admin-modal').classList.remove('hidden');
        const listEl = document.getElementById('admin-users-list');
        listEl.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-slate-500"><i class="fa-solid fa-spinner spinner mr-2"></i>Đang tải danh sách...</td></tr>`;

        try {
            const snapshot = await window.db.collection('allowed_users').get();
            listEl.innerHTML = '';
            if (snapshot.empty) {
                listEl.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-slate-400">Chưa có người dùng nào.</td></tr>`;
                return;
            }
            snapshot.forEach(doc => {
                const data = doc.data();
                const expDate = parseDate(data.expiresAt);
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
            listEl.innerHTML = `<tr><td colspan="3" class="p-4 text-center text-rose-400">Không có quyền truy cập danh sách.</td></tr>`;
        }
    }

    function closeAdminModal() {
        document.getElementById('admin-modal').classList.add('hidden');
    }
    """
