import os
import json
import pandas as pd
import numpy as np
import subprocess
import datetime

DATA_DIR = "bctc_data"
OUTPUT_CSV = "quant_screener_summary.csv"

def parse_bctc_file(filepath):
    """Đọc file JSON của 1 mã và trích xuất chỉ số các quý gần nhất"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc file {filepath}: {e}")
        return None

    ticker = os.path.basename(filepath).replace(".json", "").upper()
    
    balance_sheet = data.get("balance_sheet", [])
    income_statement = data.get("income_statement", [])

    if not balance_sheet or not income_statement:
        return None

    # Tổ chức dữ liệu dạng Dict: [period][id] = value
    bs_dict = {}
    for item in balance_sheet:
        p = item.get("period")
        if p not in bs_dict:
            bs_dict[p] = {}
        bs_dict[p][item.get("id")] = item.get("value")

    is_dict = {}
    for item in income_statement:
        p = item.get("period")
        if p not in is_dict:
            is_dict[p] = {}
        is_dict[p][item.get("id")] = item.get("value")

    periods = sorted(list(set(bs_dict.keys()).intersection(set(is_dict.keys()))), reverse=True)
    if len(periods) < 2:
        return None

    curr_p = periods[0]     # Quý gần nhất
    prev_p = periods[1]     # Quý liền trước (QoQ)
    yoy_p = f"{int(curr_p[:4])-1}-{curr_p[5:]}" # Cùng kỳ năm ngoái (YoY)

    total_assets = bs_dict[curr_p].get("BS_TOTAL_ASSETS", 0)
    loans = bs_dict[curr_p].get("BS_LOANS_TO_CUSTOMERS", 0)
    equity = bs_dict[curr_p].get("BS_EQUITY", 0)
    nii = is_dict[curr_p].get("IS_NET_INTEREST_INCOME", 0)
    pat = is_dict[curr_p].get("IS_NET_PROFIT_AFTER_TAX", 0)

    loans_prev = bs_dict.get(prev_p, {}).get("BS_LOANS_TO_CUSTOMERS", 0)
    loans_yoy = bs_dict.get(yoy_p, {}).get("BS_LOANS_TO_CUSTOMERS", 0)

    credit_growth_qoq = ((loans - loans_prev) / loans_prev * 100) if loans_prev else np.nan
    credit_growth_yoy = ((loans - loans_yoy) / loans_yoy * 100) if loans_yoy else np.nan

    pat_prev = is_dict.get(prev_p, {}).get("IS_NET_PROFIT_AFTER_TAX", 0)
    pat_yoy = is_dict.get(yoy_p, {}).get("IS_NET_PROFIT_AFTER_TAX", 0)

    pat_growth_qoq = ((pat - pat_prev) / pat_prev * 100) if pat_prev else np.nan
    pat_growth_yoy = ((pat - pat_yoy) / pat_yoy * 100) if pat_yoy else np.nan

    roe_q = (pat / equity * 100) if equity else np.nan

    return {
        "Mã CK": ticker,
        "Kỳ báo cáo": curr_p,
        "Tổng tài sản (Tỷ VNĐ)": round(total_assets / 1e9, 2) if total_assets else 0,
        "Dư nợ cho vay (Tỷ VNĐ)": round(loans / 1e9, 2) if loans else 0,
        "Vốn chủ sở hữu (Tỷ VNĐ)": round(equity / 1e9, 2) if equity else 0,
        "Thu nhập lãi thuần (Tỷ VNĐ)": round(nii / 1e9, 2) if nii else 0,
        "LNST (Tỷ VNĐ)": round(pat / 1e9, 2) if pat else 0,
        "TT Tín dụng QoQ (%)": round(credit_growth_qoq, 2) if pd.notnull(credit_growth_qoq) else "—",
        "TT Tín dụng YoY (%)": round(credit_growth_yoy, 2) if pd.notnull(credit_growth_yoy) else "—",
        "TT LNST QoQ (%)": round(pat_growth_qoq, 2) if pd.notnull(pat_growth_qoq) else "—",
        "TT LNST YoY (%)": round(pat_growth_yoy, 2) if pd.notnull(pat_growth_yoy) else "—",
        "ROE Quý (%)": round(roe_q, 2) if pd.notnull(roe_q) else "—"
    }

def auto_git_push():
    try:
        print("\n📤 Đang đồng bộ file tổng hợp lên GitHub...")
        subprocess.run(["git", "add", OUTPUT_CSV], check=True)
        commit_msg = f"Auto update quant screener summary - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Đẩy dữ liệu lên GitHub thành công!")
    except Exception as e:
        print(f"ℹ️ Git push info (có thể do không có thay đổi mới hoặc lỗi xác thực): {e}")

def main():
    if not os.path.exists(DATA_DIR):
        print(f"⚠️ Thư mục '{DATA_DIR}' không tồn tại.")
        return

    results = []
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

    if not files:
        print(f"⚠️ Không tìm thấy file JSON nào.")
        return

    print(f"🔄 Đang xử lý tính toán cho {len(files)} mã cổ phiếu...")
    for file_name in files:
        file_path = os.path.join(DATA_DIR, file_name)
        res = parse_bctc_file(file_path)
        if res:
            results.append(res)

    df = pd.DataFrame(results)
    
    if not df.empty:
        df = df.sort_values(by="LNST (Tỷ VNĐ)", ascending=False)
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        
        print("\n✅ TỔNG HỢP SỐ LIỆU THÀNH CÔNG:")
        print("=" * 100)
        print(df.head(10).to_string(index=False)) # In trước 10 mã đầu tiên
        print("=" * 100)
        print(f"📁 Đã lưu file: {OUTPUT_CSV}")

        # Tự động đẩy lên git
        auto_git_push()

if __name__ == "__main__":
    main()
