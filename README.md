# Investing
1-Step: Lấy BCTC: crawl_bctc.py⁠ (PC)
2-Step: Lấy dữ liệu giá: fetch_data_local.py (PC)
3-Step: Lọc & Sắp xếp: advanced_screener.py
4-Step: Đánh giá AI: analyze_ai.py
4.5Step: Tính lợi nhuận: simulator.py
5-Step: Build: render_ui.py

#AI
1. Chạy top đầu mỗi ngành (khoảng 35 mã, không chia batch):
python ai_analysis.py --mode top
 
2. Chạy phần còn lại, chia 5 batch — lần lượt:
python ai_analysis.py --mode rest --total-batches 5 --batch 1
python ai_analysis.py --mode rest --total-batches 5 --batch 2
python ai_analysis.py --mode rest --total-batches 5 --batch 3
python ai_analysis.py --mode rest --total-batches 5 --batch 4
python ai_analysis.py --mode rest --total-batches 5 --batch 5
 
3. Chạy tất cả một lần (top trước, rồi hết phần còn lại nếu chỉ 1 batch):
python ai_analysis.py --mode all --total-batches 1
 
4. Chạy theo danh sách nhập tay qua biến môi trường (như cũ):
INPUT_SYMBOLS="ACB,FPT,MWG" python ai_analysis.py
