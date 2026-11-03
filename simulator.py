import os
import json
import pandas as pd

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
    gom nhóm theo Quý, lấy giá trung bình (mean) và tính CAGR chuẩn xác theo thời gian thực (ngày).
    Có thêm tham số verbose để in ra thông tin giá trung bình quý đầu và quý cuối nếu cần.
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
        
        # 1. Xác định mốc ngày mới nhất và lùi chính xác đúng 5 năm (theo lịch ngày thực tế)
        max_date = df['date'].max()
        cutoff_date = max_date - pd.DateOffset(years=5)
        
        # Lọc dữ liệu nằm trong đúng khung 5 năm thực tế gần nhất
        df_5years = df[df['date'] >= cutoff_date]
        
        if len(df_5years) < 30:
            return 0.15 
            
        # 2. Tạo cột gom nhóm theo Năm-Quý (VD: 2021Q4, 2022Q1...)
        df_5years['year_quarter'] = df_5years['date'].dt.to_period('Q')
        
        # 3. Gom nhóm theo Quý: Tính giá trung bình (mean) và lấy ngày đầu tiên của quý đó làm mốc đại diện
        df_quarterly = df_5years.groupby('year_quarter').agg({
            'close': 'mean',
            'date': 'first'
        }).reset_index()
        
        if len(df_quarterly) < 2:
            return 0.15
            
        # 4. Lấy điểm đầu (quý cũ nhất trong khung 5 năm) và điểm cuối (quý mới nhất)
        start_row = df_quarterly.iloc[0]
        end_row = df_quarterly.iloc[-1]
        
        start_price = start_row['close']
        end_price = end_row['close']
        
        start_date = start_row['date']
        end_date = end_row['date']
        
        start_q = str(start_row['year_quarter'])
        end_q = str(end_row['year_quarter'])
        
        # Nếu bật chế độ verbose, in ra thông tin chi tiết giá trung bình quý
        if verbose:
            print(f"[{symbol}] Quý đầu ({start_q}): Giá TB = {start_price:.2f} | Quý cuối ({end_q}): Giá TB = {end_price:.2f}")

        # 5. Tính chính xác số năm dựa trên số ngày thực tế giữa 2 mốc thời gian
        days = (end_date - start_date).days
        if days < 30:
            return 0.15
            
        years = days / 365.25  # Quy đổi ra năm chính xác có tính năm nhuận
        if years <= 0:
            return 0.15
            
        # 6. Tính CAGR chuẩn theo công thức lãi kép thời gian thực
        cagr = (end_price / start_price) ** (1 / years) - 1
        
        # Giới hạn biên độ an toàn (từ -50% đến +100%/năm)
        cagr = max(-0.5, min(cagr, 1.0))
        return round(cagr, 4)
        
    except Exception as e:
        print(f"⚠️ Lỗi tính lịch sử cho {symbol}: {e}")
        return 0.15

def run_symbol_specific_simulation(symbol, initial_capital, monthly_contribution, years):
    """
    Giả lập riêng cho một mã dựa trên hiệu suất thực tế trong quá khứ của nó.
    """
    historical_rate = get_historical_return_rate(symbol, verbose=True)
    
    is_fallback = False
    if historical_rate is None:
        historical_rate = 0.15 
        is_fallback = True
        
    sim_result = calculate_dca_investment(initial_capital, monthly_contribution, years, historical_rate)
    
    return {
        "symbol": symbol,
        "estimated_annual_rate_percent": round(historical_rate * 100, 2),
        "is_fallback": is_fallback,
        "simulation": sim_result
    }

def run_complex_backtest_simulation(history_dir="history", output_json="symbol_sim_rates.json"):
    """
    Quét toàn bộ thư mục history/ để tính lãi suất quá khứ (CAGR theo Quý trong 5 năm) của TỪNG MÃ,
    sau đó lưu ra file symbol_sim_rates.json để Front-end đọc.
    """
    rates_map = {}
    
    if os.path.exists(history_dir):
        for filename in os.listdir(history_dir):
            if filename.endswith(".json"):
                symbol = filename.replace(".json", "")
                # Bật verbose=True để in ra giá trung bình quý kiểm chứng trực tiếp trên màn hình terminal
                cagr = get_historical_return_rate(symbol, history_dir, verbose=True)
                if cagr is not None:
                    rates_map[symbol] = {
                        "annual_rate_percent": round(cagr * 100, 2)
                    }
                    
    # Lưu ra file JSON phục vụ Front-end
    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(rates_map, f, ensure_ascii=False, indent=4)
        print(f"✅ Đã tính toán và lưu thành công lãi suất (theo Quý/5 năm) cho {len(rates_map)} mã vào {output_json}")
    except Exception as e:
        print(f"⚠️ Không thể ghi file {output_json}: {e}")

    return {
        "status": "success",
        "total_symbols_calculated": len(rates_map),
        "default_benchmark_return": 15.0
    }

if __name__ == "__main__":
    run_complex_backtest_simulation()
