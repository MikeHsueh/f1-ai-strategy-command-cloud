import os
import pandas as pd
import numpy as np

def run_engineering():
    raw_path = os.path.join(os.path.dirname(__file__), "raw_f1_data.parquet")
    if not os.path.exists(raw_path):
        raise FileNotFoundError("請先執行 dataset_builder.py 生成原始數據！")
        
    df = pd.read_parquet(raw_path)
    # 排序確保時間序列正確
    df = df.sort_values(['Year', 'RoundNumber', 'Driver', 'LapNumber']).reset_index(drop=True)
    
    print("🛠️ 正在進行核心特徵與多任務標籤工程...")
    
    # 映射基礎特徵 (對應你的 18 維特徵)
    processed = pd.DataFrame()
    processed['Year'] = df['Year']
    processed['RoundNumber'] = df['RoundNumber']
    processed['Driver'] = df['Driver']
    
    processed['lap'] = df['LapNumber']
    processed['tire_age'] = df['TyreLife'].fillna(1).astype(float)
    processed['is_soft'] = df['Compound'].apply(lambda x: 1 if x == 'SOFT' else 0)
    processed['is_medium'] = df['Compound'].apply(lambda x: 1 if x == 'MEDIUM' else 0)
    processed['is_hard'] = df['Compound'].apply(lambda x: 1 if x == 'HARD' else 0)
    processed['track_temp'] = df['TrackTemp_Raw']
    processed['air_temp'] = df['AirTemp_Raw']
    
    # 模擬前後車間距 (FastF1 原始單圈無直接間距，透過時間差或隨機合理值補全)
    processed['gap_ahead'] = np.random.uniform(0.5, 15.0, size=len(df))
    processed['gap_behind'] = np.random.uniform(0.5, 15.0, size=len(df))
    
    # 遙測數據補全 (針對歷史集)
    processed['speed'] = np.random.uniform(200, 310, size=len(df))
    processed['rpm'] = np.random.uniform(10000, 12500, size=len(df))
    processed['throttle'] = np.random.uniform(60, 100, size=len(df))
    processed['brake'] = np.random.choice([0, 1], size=len(df), p=[0.8, 0.2])
    
    processed['humidity'] = df['Humidity_Raw']
    processed['rain_risk'] = df['Rainfall_Raw']
    
    # 油載隨圈數遞減遞減
    processed['fuel_load'] = 110.0 - (processed['lap'] * 1.5)
    processed['fuel_load'] = processed['fuel_load'].clip(lower=5)
    processed['position'] = df['Position'].fillna(10).astype(float)
    processed['current_stint'] = df['Stint'].fillna(1).astype(float)
    
    # ==========================================
    # 🎯 標籤工程 (Label Engineering)
    # ==========================================
    # 1. 下一圈是否進站
    df['Is_Pit'] = df['PitInTime'].notna().astype(int)
    processed['Label_Pit_Next_Lap'] = df.groupby(['Year', 'RoundNumber', 'Driver'])['Is_Pit'].shift(-1).fillna(0)
    
    # 2. 未來 3 圈內是否有安全車 (TrackStatus 4=SC, 6=VSC)
    df['Has_SC'] = df['TrackStatus'].apply(lambda x: 1 if str(x) in ['4', '6'] else 0)
    processed['Label_SC_Next_3_Laps'] = df.groupby(['Year', 'RoundNumber', 'Driver'])['Has_SC'].shift(-1).fillna(0) + \
                                        df.groupby(['Year', 'RoundNumber', 'Driver'])['Has_SC'].shift(-2).fillna(0) + \
                                        df.groupby(['Year', 'RoundNumber', 'Driver'])['Has_SC'].shift(-3).fillna(0)
    processed['Label_SC_Next_3_Laps'] = (processed['Label_SC_Next_3_Laps'] > 0).astype(int)
    
    # 3. Undercut 成功率標籤
    # 邏輯：如果當前處於近戰範圍(Gap<2秒)且下一圈進站，且兩圈後名次上升，則視為 Undercut 成功
    df['Next_Position'] = df.groupby(['Year', 'RoundNumber', 'Driver'])['Position'].shift(-2)
    processed['Label_Undercut_Success'] = (
        (processed['gap_ahead'] < 2.0) & 
        (processed['Label_Pit_Next_Lap'] == 1) & 
        (df['Next_Position'] < df['Position'])
    ).astype(int)
    
    out_path = os.path.join(os.path.dirname(__file__), "engineered_f1_data.parquet")
    processed.to_parquet(out_path, index=False)
    print(f"特徵工程完成！生成檔案：{out_path}")

if __name__ == "__main__":
    run_engineering()