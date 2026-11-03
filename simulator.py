# simulator.py
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

def get_historical_return_rate(symbol, history_dir="history"):
    """
    Đọc file lịch sử giá của một mã (vd: history/VIC.json) để tính tỷ suất sinh lời thực tế (CAGR) trong quá khứ.
    """
    file_path = os.path.join(history_dir, f"{symbol}.json")
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Lấy dữ liệu biểu đồ ngày (history_d1)
        history_bars = data.get("history_d1", [])
        if len(history_bars) < 50:
            return 0.15 # Mặc định nếu thiếu dữ liệu
            
        df = pd.DataFrame(history_bars)
        # Chuyển đổi định dạng thời gian/ngày tháng
        df['date'] = pd.to_datetime(df['time'])
        df = df.sort_values('date')
        
        start_price = df.iloc[0]['close']
        end_price = df.iloc[-1]['close']
        
        start_date = df.iloc[0]['date']
        end_date = df.iloc[-1]['date']
        
        days = (end_date - start_date).days
        if days < 30:
            return 0.15 # Mặc định nếu khoảng thời gian quá ngắn
            
        years = days / 365.25
        if years <= 0:
            return 0.15
            
        # Tính tỷ suất sinh lời hàng năm (CAGR) dựa trên giá lịch sử thực tế
        cagr = (end_price / start_price) ** (1 / years) - 1
        
        # Giới hạn mức hợp lý để tránh biên độ quá dị (từ -50% đến +100%/năm)
        cagr = max(-0.5, min(cagr, 1.0))
        return round(cagr, 4)
        
    except Exception as e:
        print(f"⚠️ Lỗi tính lịch sử cho {symbol}: {e}")
        return 0.15

def run_symbol_specific_simulation(symbol, initial_capital, monthly_contribution, years):
    """
    Giả lập riêng cho một mã dựa trên hiệu suất thực tế trong quá khứ của nó.
    """
    historical_rate = get_historical_return_rate(symbol)
    
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
    Quét tất cả các file trong thư mục history/ để tính lãi suất quá khứ (CAGR) của từng mã,
    sau đó lưu ra file JSON để giao diện web (render_ui.py) có thể đọc và nạp vào modal.
    """
    rates_map = {}
    
    if os.path.exists(history_dir):
        for filename in os.listdir(history_dir):
            if filename.endswith(".json"):
                symbol = filename.replace(".json", "")
                cagr = get_historical_return_rate(symbol, history_dir)
                if cagr is not None:
                    rates_map[symbol] = {
                        "annual_rate_percent": round(cagr * 100, 2)
                    }
                    
    # Lưu ra file JSON phục vụ Front-end
    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(rates_map, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ Không thể ghi file {output_json}: {e}")

    return {
        "status": "success",
        "total_symbols_calculated": len(rates_map),
        "default_benchmark_return": 15.0
    }

if __name__ == "__main__":
    # Test thử nghiệm quét và tính toán toàn bộ mã
    summary = run_complex_backtest_simulation()
    print(f"📊 Đã quét và tính toán xong lãi suất lịch sử cho {summary.get('total_symbols_calculated', 0)} mã.")
    
    # Test thử nghiệm riêng cho mã VIC
    res = run_symbol_specific_simulation("VIC", initial_capital=20000000, monthly_contribution=3000000, years=3)
    print("📈 KẾT QUẢ GIẢ LẬP RIÊNG CHO MÃ VIC:", res)
