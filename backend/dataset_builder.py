import os
import fastf1
import pandas as pd
from tqdm import tqdm
import numpy as np

CACHE_DIR = os.path.join(os.path.dirname(__file__), 'fastf1_cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

def build_dataset(start_year=2022, end_year=2024):
    print("開始下載真實 F1 歷史數據...")
    all_laps = []
    
    for year in range(start_year, end_year + 1):
        try:
            schedule = fastf1.get_event_schedule(year)
            races = schedule[schedule['EventFormat'] != 'testing']
        except Exception as e:
            print(f"無法獲取 {year} 賽程: {e}")
            continue
            
        for _, row in tqdm(races.iterrows(), total=races.shape[0], desc=f"Season {year}"):
            r_num = row['RoundNumber']
            if r_num == 0: continue
            try:
                session = fastf1.get_session(year, r_num, 'R')
                session.load(laps=True, telemetry=False, weather=True)
                laps = session.laps.copy()
                if laps.empty: continue
                
                # 注入元數據
                laps['Year'] = year
                laps['RoundNumber'] = r_num
                
                # 處理天氣
                w = session.weather_data
                laps['TrackTemp_Raw'] = w['TrackTemp'].mean() if not w.empty else 25.0
                laps['AirTemp_Raw'] = w['AirTemp'].mean() if not w.empty else 20.0
                laps['Humidity_Raw'] = w['Humidity'].mean() if not w.empty else 50.0
                laps['Rainfall_Raw'] = 100.0 if (not w.empty and w['Rainfall'].any()) else 0.0
                
                all_laps.append(laps)
            except Exception as e:
                continue

    if all_laps:
        df = pd.concat(all_laps, ignore_index=True)
        out_path = os.path.join(os.path.dirname(__file__), "raw_f1_data.parquet")
        df.to_parquet(out_path, index=False)
        print(f"成功儲存原始數據至 {out_path}，共 {len(df)} 筆單圈紀錄。")
    else:
        print("未抓取到任何數據")

if __name__ == "__main__":
    build_dataset(2022, 2024)