import os
import json
import pandas as pd
import datetime
import subprocess

def calculate_dca_investment(initial_capital, monthly_contribution, years, annual_return_rate):
    """
    Hàm tính toán lãi kép & tích sản định kỳ (DCA) chung.
    """
    monthly_rate = annual_return_rate / 12
    total_months = years * 12
    
    total_principal = initial_capital + (monthly_contribution * total_months)
    future_val = initial_capital * ((1 + annual_return_rate) ** years)
    
    for i in range(1, total_months + 1):
        future_val += monthly_contribution * ((1 + monthly_rate) ** (total_months - i + 1))
        
    profit = future_val - total_principal
    
    return {
        "principal": round(total_principal),
        "profit": round(profit),
        "total_future_value": round(future_val),
        "roi_percent": round((profit / total_principal) * 100, 2) if total_principal > 0 else 0
    }

def get_historical_return_rate(symbol, history_dir="history", verbose=False):
    """
    Đọc file lịch sử giá của một mã, lọc đúng 5 năm tính theo ngày thực tế,
    gom nhóm theo Quý, lấy giá trung bình (mean) và tính CAGR chuẩn xác.
    """
    file_path = os.path.join(history_dir, f"{symbol}.json")
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        history_bars = data.get("history_d1", [])
        if len(history_bars) < 30:
            return 0.15 # Mặc định nếu thiếu dữ liệu
            
        df = pd.DataFrame(history_bars)
        df['date'] = pd.to_datetime(df['time'])
        df = df.sort_values('date')
        
        # 1. Xác định mốc ngày mới nhất và lùi chính xác đúng 5 năm
        max_date = df['date'].max()
        cutoff_date = max_date - pd.DateOffset(years=5)
        
        # Sử dụng .loc và .copy() để khắc phục triệt để SettingWithCopyWarning
        df_5years = df.loc[df['date'] >= cutoff_date].copy()
        
        if len(df_5years) < 30:
            return 0.15 
            
        # 2. Tạo cột gom nhóm theo Năm-Quý an toàn bằng .loc
        df_5years.loc[:, 'year_quarter'] = df_5years['date'].dt.to_period('Q')
        
        # 3. Gom nhóm theo Quý: Tính giá trung bình (mean)
        df_quarterly = df_5years.groupby('year_quarter').agg({
            'close': 'mean',
            'date': 'first'
        }).reset_index()
        
        if len(df_quarterly) < 2:
            return 0.15
            
        # 4. Lấy điểm đầu và điểm cuối trong khung 5 năm
        start_row = df_quarterly.iloc[0]
        end_row = df_quarterly.iloc[-1]
        
        start_price = start_row['close']
        end_price = end_row['close']
        
        start_date = start_row['date']
        end_date = end_row['date']
        
        start_q = str(start_row['year_quarter'])
        end_q = str(end_row['year_quarter'])
        
        if verbose:
            print(f"[{symbol}] Quý đầu ({start_q}): Giá TB = {start_price:.2f} | Quý cuối ({end_q}): Giá TB = {end_price:.2f}")

        # 5. Tính số năm thực tế dựa trên khoảng cách ngày
        days = (end_date - start_date).days
        if days < 30:
            return 0.15
            
        years = days / 365.25
        if years <= 0:
            return 0.15
            
        # 6. Tính CAGR chuẩn theo công thức lãi kép thời gian thực
        cagr = (end_price / start_price) ** (1 / years) - 1
        cagr = max(-0.5, min(cagr, 1.0))
        return round(cagr, 4)
        
    except Exception as e:
        print(f"⚠️ Lỗi tính lịch sử cho {symbol}: {e}")
        return 0.15

def auto_git_push(output_json):
    """Tự động cập nhật, commit và push file symbol_sim_rates.json lên GitHub"""
    try:
        print("📤 Đang tiến hành đồng bộ file kết quả lên GitHub...")
        subprocess.run(["git", "add", output_json], check=True)
        commit_msg = f"Auto update symbol_sim_rates.json - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "pull", "origin", "main", "--rebase"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 Đã đẩy file symbol_sim_rates.json lên GitHub thành công!")
    except subprocess.CalledProcessError:
        print("⚠️ Git: Đã đồng bộ hoặc không có thay đổi mới cần đẩy.")
    except Exception as e:
        print(f"⚠️ Lỗi Git push: {e}")

def run_complex_backtest_simulation(history_dir="history", output_json="symbol_sim_rates.json"):
    """
    Quét toàn bộ thư mục history/ để tính lãi suất quá khứ (CAGR theo Quý trong 5 năm) của TỪNG MÃ,
    sau đó ghi đè ra file symbol_sim_rates.json và tự động đẩy lên GitHub.
    """
    rates_map = {}
    
    if os.path.exists(history_dir):
        for filename in sorted(os.listdir(history_dir)):
            if filename.endswith(".json"):
                symbol = filename.replace(".json", "")
                cagr = get_historical_return_rate(symbol, history_dir, verbose=True)
                if cagr is not None:
                    rates_map[symbol] = {
                        "annual_rate_percent": round(cagr * 100, 2)
                    }
                    
    # Ghi đè hoàn toàn file JSON mới nhất
    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(rates_map, f, ensure_ascii=False, indent=4)
        print(f"✅ Đã ghi đè thành công file {output_json} với {len(rates_map)} mã!")
    except Exception as e:
        print(f"⚠️ Không thể ghi file {output_json}: {e}")

    # Tự động đẩy lên GitHub ngay lập tức
    auto_git_push(output_json)

    return {
        "status": "success",
        "total_symbols_calculated": len(rates_map),
        "default_benchmark_return": 15.0
    }

if __name__ == "__main__":
    run_complex_backtest_simulation()
