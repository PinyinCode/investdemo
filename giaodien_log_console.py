# -*- coding: utf-8 -*-
"""giaodien_log_console.py — Khung log nổi (refresh giá)."""


def build_log_console_html():
    return r"""
    <!-- KHUNG LOG NỔI -->
    <div id="log-console" class="fixed bottom-4 right-4 w-80 md:w-96 bg-slate-900/95 backdrop-blur border border-slate-700 rounded-xl shadow-2xl z-[9999] overflow-hidden flex flex-col transition-all duration-300 transform translate-y-full opacity-0 hidden">
        <div class="bg-slate-950 px-3 py-2 border-b border-slate-800 flex justify-between items-center cursor-pointer" onclick="toggleLogConsole()">
            <span class="text-xs font-bold text-slate-300 flex items-center gap-1.5"><i class="fa-solid fa-terminal text-emerald-400"></i> Tiến trình cập nhật</span>
            <div class="flex items-center gap-2">
                <span id="log-status-badge" class="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Chờ</span>
                <button type="button" onclick="clearLog(event)" class="text-slate-500 hover:text-white transition" title="Xóa log"><i class="fa-solid fa-trash-can text-[10px]"></i></button>
                <button type="button" class="text-slate-500 hover:text-white transition" title="Thu nhỏ / Mở rộng"><i class="fa-solid fa-chevron-down text-[10px]" id="log-chevron"></i></button>
            </div>
        </div>
        <div class="w-full bg-slate-800 h-1">
            <div id="log-progress-bar" class="bg-emerald-500 h-1 transition-all duration-300" style="width: 0%;"></div>
        </div>
        <div id="log-content" class="p-2 overflow-y-auto text-[11px] font-mono leading-relaxed space-y-1 h-48 text-slate-300"></div>
    </div>
    """
