# F1 AI Strategy Command

Professional Vue 3 race strategy dashboard backed by the trained
BiLSTM-Attention 40-feature model.

## Stack

- Vue 3 + Vite + TypeScript
- Pinia + Vue Router
- Axios with automatic mock fallback
- ECharts
- Flask + PyTorch backend

## Pages

- `/` Dashboard
- `/replay` Race replay and lap timeline
- `/simulator` What-if strategy simulator
- `/model-analysis` Feature importance and model health

## Local Run

Use `start-dashboard.bat`, or run the services separately:

```powershell
cd C:\Users\leow3\frontend-app\backend
C:\Users\leow3\anaconda3\python.exe run_server.py
```

```powershell
cd C:\Users\leow3\frontend-app
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

The Vite development server proxies `/api` to the Flask backend on port 5000.

## Mock Mode

Mock mode is deterministic and uses the same frontend data contract:

```powershell
npm.cmd run dev:mock
```

Set `VITE_USE_MOCK=true` in a Vite environment file to force mock mode.
When mock mode is not forced, every API module automatically falls back to
mock data if its backend request fails.

## Cloud Deployment

The production build is a single service: Flask serves the compiled Vue
application and the API. See `DEPLOYMENT.md` for Docker, Render, Railway,
and generic cloud instructions.

## Verification

```powershell
npm.cmd run typecheck
npm.cmd run build
npm.cmd run build:mock
```
