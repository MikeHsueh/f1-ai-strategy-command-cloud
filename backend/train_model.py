import os
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset, DataLoader
from strategy_model import F1StrategyNet, device

# =========================================================
# 1. 載入特徵工程數據與時序切分
# =========================================================
data_path = os.path.join(os.path.dirname(__file__), "engineered_f1_data.parquet")
if not os.path.exists(data_path):
    print("找不到特徵數據，自動為您啟動數據流生成...")
    import dataset_builder, feature_engineering
    dataset_builder.build_dataset()
    feature_engineering.run_engineering()

df = pd.read_parquet(data_path)

feature_cols = [
    'lap', 'tire_age', 'is_soft', 'is_medium', 'is_hard', 'track_temp', 'air_temp',
    'gap_ahead', 'gap_behind', 'speed', 'rpm', 'throttle', 'brake', 'humidity',
    'rain_risk', 'fuel_load', 'position', 'current_stint'
]

# 標準化特徵
scaler = StandardScaler()
df[feature_cols] = scaler.fit_transform(df[feature_cols])
joblib.dump(scaler, os.path.join(os.path.dirname(__file__), 'scaler.pkl'))
print('scaler.pkl 儲存成功')

# =========================================================
# 2. 建立 LSTM 時序 Dataset (長度 = 5)
# =========================================================
class F1SequenceDataset(Dataset):
    def __init__(self, data_df, feat_cols, seq_len=5):
        self.x_list = []
        self.y_pit = []
        self.y_sc = []
        self.y_udc = []
        
        grouped = data_df.groupby(['Year', 'RoundNumber', 'Driver'])
        for _, group in grouped:
            group = group.sort_values('lap')
            feats = group[feat_cols].values
            p_lbl = group['Label_Pit_Next_Lap'].values
            s_lbl = group['Label_SC_Next_3_Laps'].values
            u_lbl = group['Label_Undercut_Success'].values
            
            if len(feats) < seq_len: continue
            for i in range(len(feats) - seq_len + 1):
                self.x_list.append(feats[i:i+seq_len])
                self.y_pit.append(p_lbl[i+seq_len-1])
                self.y_sc.append(s_lbl[i+seq_len-1])
                self.y_udc.append(u_lbl[i+seq_len-1])
                
        self.x_list = torch.tensor(np.array(self.x_list), dtype=torch.float32)
        self.y_pit = torch.tensor(np.array(self.y_pit), dtype=torch.float32)
        self.y_sc = torch.tensor(np.array(self.y_sc), dtype=torch.float32)
        self.y_udc = torch.tensor(np.array(self.y_udc), dtype=torch.float32)

    def __len__(self): return len(self.y_pit)
    def __getitem__(self, idx):
        return self.x_list[idx], self.y_pit[idx], self.y_sc[idx], self.y_udc[idx]

dataset = F1SequenceDataset(df, feature_cols, seq_len=5)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

# =========================================================
# 3. 多任務訓練迴圈
# =========================================================
model = F1StrategyNet(input_dim=18).to(device)
criterion = nn.BCEWithLogitsLoss() # 比 BCELoss 對數值更穩定
optimizer = optim.Adam(model.parameters(), lr=0.001)

EPOCHS = 15
best_loss = float('inf')

print("進入真實多賽季數據多任務模型訓練...")
for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    for xb, y_pit, y_sc, y_udc in loader:
        xb, y_pit, y_sc, y_udc = xb.to(device), y_pit.to(device), y_sc.to(device), y_udc.to(device)
        
        optimizer.zero_grad()
        p_out, s_out, u_out = model(xb)
        
        # 聯合多元 Loss 計算
        loss_pit = criterion(p_out.squeeze(), y_pit)
        loss_sc = criterion(s_out.squeeze(), y_sc)
        loss_udc = criterion(u_out.squeeze(), y_udc)
        
        loss = loss_pit + 0.5 * loss_sc + 0.8 * loss_udc
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
    avg_loss = total_loss / len(loader)
    print(f"Epoch {epoch+1:02d}/{EPOCHS} | Combined Loss: {avg_loss:.4f}")
    
    if avg_loss < best_loss:
        best_loss = avg_loss
        torch.save(model.state_dict(), os.path.join(os.path.dirname(__file__), 'best_model.pth'))
        print('⭐ 最佳模型 best_model.pth 權重已更新更新')

print("真實數據多任務訓練圓滿完成！")