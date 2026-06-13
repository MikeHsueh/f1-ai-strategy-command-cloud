import os

import torch
import torch.nn as nn


torch.set_num_threads(max(1, int(os.getenv("TORCH_NUM_THREADS", "1"))))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_NAME = "BiLSTM-Attention-40F"
MODEL_INPUT_DIM = 40
MODEL_SEQUENCE_LENGTH = 5
MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_f1_strategy_model_attention.pth")

MODEL_LOADED = False
MODEL_LOAD_ERROR = None


class TemporalAttention(nn.Module):
    def __init__(self, input_dim, attention_dim=128, dropout=0.2):
        super().__init__()
        self.score = nn.Sequential(
            nn.Linear(input_dim, attention_dim),
            nn.Tanh(),
            nn.Dropout(dropout),
            nn.Linear(attention_dim, 1),
        )

    def forward(self, sequence_output):
        attention_logits = self.score(sequence_output).squeeze(-1)
        attention_weights = torch.softmax(attention_logits, dim=1)
        context = torch.sum(sequence_output * attention_weights.unsqueeze(-1), dim=1)
        return context, attention_weights


class F1StrategyModel(nn.Module):
    def __init__(self, input_size=40, hidden_size=128, num_layers=2, dropout=0.35):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
            bidirectional=True,
        )

        lstm_dim = hidden_size * 2
        self.sequence_norm = nn.LayerNorm(lstm_dim)
        self.attention = TemporalAttention(
            input_dim=lstm_dim,
            attention_dim=hidden_size,
            dropout=dropout,
        )

        self.head = nn.Sequential(
            nn.LayerNorm(lstm_dim),
            nn.Linear(lstm_dim, 64),
            nn.GELU(),
            nn.Dropout(0.30),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(32, 1),
        )

    def forward(self, x, return_attention=False):
        sequence_output, _ = self.lstm(x)
        sequence_output = self.sequence_norm(sequence_output)
        context, attention_weights = self.attention(sequence_output)
        logits = self.head(context).squeeze(-1)

        if return_attention:
            return logits, attention_weights

        return logits


model = F1StrategyModel(input_size=MODEL_INPUT_DIM).to(device)

if os.path.exists(MODEL_PATH):
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        MODEL_LOADED = True
        print("Loaded trained model: best_f1_strategy_model_attention.pth")
    except Exception as exc:
        MODEL_LOAD_ERROR = str(exc)
        print(f"Model weights were not loaded. Reason: {MODEL_LOAD_ERROR}")
else:
    MODEL_LOAD_ERROR = "best_f1_strategy_model_attention.pth not found"

model.eval()

MODEL_INFO = {
    "name": MODEL_NAME,
    "input_dim": MODEL_INPUT_DIM,
    "sequence_length": MODEL_SEQUENCE_LENGTH,
    "weights_loaded": MODEL_LOADED,
    "device": str(device),
    "weights_path": MODEL_PATH,
    "load_error": MODEL_LOAD_ERROR,
}
