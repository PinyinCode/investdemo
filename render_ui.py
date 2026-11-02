import json
import os

SCREENER_FILE = "screener_results.json"
OUTPUT_HTML = "index.html"

def generate_html():
    if not os.path.exists(SCREENER_FILE):
        print(f"❌ Không tìm thấy file {SCREENER_FILE}")
        return

    with open(SCREENER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 🎨 ĐỊNH NGHĨA GIAO DIỆN & MODULES BẰNG PYTHON
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pro Quant Screener - VN100</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans pb-10">
    <header class="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <div class="bg-emerald-600 text-white p-2 rounded-lg shadow-lg">
                    <i class="fa-solid fa-scale-balanced text-lg"></i>
                </div>
                <div>
                    <h1 class="text-base md:text-lg font-bold text-white">Pro Quant Screener</h1>
                    <p class="text-[10px] text-slate-400">Hệ thống AI Tích sản & Định lượng 7 Nhóm Ngành</p>
                </div>
            </div>
            <span class="text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 font-semibold">
                🟢 Đã cập nhật tự động qua Workflow
            </span>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- KHU VỰC HIỂN THỊ DỮ LIỆU ĐƯỢC RENDER TỪ PYTHON -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" id="stock-grid">
"""

    # Vòng lặp sinh các card cổ phiếu tự động từ Python
    for item in data:
        symbol = item.get("symbol", "")
        sector = item.get("sector", "")
        close_price = item.get("close_price", 0)
        pe = item.get("pe", 0)
        pb = item.get("pb", 0)
        roe = item.get("roe", 0)
        total_score = item.get("total_score", 0)
        zone = item.get("potential_zone", "")

        html_content += f"""
            <div class="bg-slate-900 rounded-xl border border-slate-800 p-4 shadow-lg hover:border-emerald-500/50 transition">
                <div class="flex justify-between items-start mb-3">
                    <div>
                        <span class="text-xl font-black text-white">{symbol}</span>
                        <span class="block text-[10px] text-slate-400">{sector}</span>
                    </div>
                    <div class="text-right">
                        <span class="block text-base font-bold text-emerald-400">{close_price:,.0f} VNĐ</span>
                        <span class="text-[10px] text-amber-400 font-semibold">Tổng điểm: {total_score}đ</span>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-2 bg-slate-950 p-2 rounded-lg text-center text-xs mb-3">
                    <div><span class="text-[9px] text-slate-500 block">P/E</span><span class="font-bold text-slate-200">{pe:.1f}</span></div>
                    <div><span class="text-[9px] text-slate-500 block">P/B</span><span class="font-bold text-slate-200">{pb:.1f}</span></div>
                    <div><span class="text-[9px] text-slate-500 block">ROE</span><span class="font-bold text-blue-400">{roe:.1f}%</span></div>
                </div>
                <div class="text-[10px] bg-indigo-500/10 text-indigo-300 p-2 rounded border border-indigo-500/20 text-center font-medium">
                    {zone}
                </div>
            </div>
"""

    html_content += """
        </div>
    </main>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Đã tự động render thành công giao diện mới ra file {OUTPUT_HTML} từ Python!")

if __name__ == "__main__":
    generate_html()
