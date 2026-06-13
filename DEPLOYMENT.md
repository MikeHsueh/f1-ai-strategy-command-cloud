# Cloud Deployment

The application is packaged as one web service:

- Vue 3 is compiled into `dist/`.
- Flask serves both the frontend and `/api`.
- The trained attention model and required Parquet datasets are included.
- `fastf1_cache/` is excluded because it is a rebuildable local cache.

## Recommended: Docker

Build and run locally:

```bash
docker build -t f1-ai-strategy-command .
docker run --rm -p 8080:8080 -e PORT=8080 f1-ai-strategy-command
```

Open `http://localhost:8080`.

The same Dockerfile can be deployed to Render, Railway, Fly.io, Google
Cloud Run, Azure Container Apps, or AWS App Runner. Configure:

- Container port: the platform-provided `PORT`, or `8080`
- Health check: `/api/health`
- Minimum memory: 2 GB recommended for PyTorch and pandas
- Persistent disk: not required for inference

## Render

1. Upload the project to a Git repository.
2. In Render, select **New > Blueprint**.
3. Select the repository containing `render.yaml`.
4. Deploy the `f1-ai-strategy-command` service.

## Railway

1. Create a project from the repository.
2. Railway detects the root `Dockerfile`.
3. Add no frontend API URL: production uses same-origin `/api`.
4. Generate a public domain after deployment.

## Non-Docker Platforms

Build command:

```bash
npm ci && npm run build && pip install -r backend/requirements.txt
```

Start command:

```bash
gunicorn --chdir backend --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
```

## Production Notes

- Do not set `VITE_USE_MOCK=true` in production.
- The default API base URL is `/`, so frontend and backend share one origin.
- `best_f1_strategy_model_attention.pth` is the active trained model.
- `raw_f1_data.parquet` and `engineered_f1_data.parquet` are required.
- The first container start can be slower while PyTorch loads the model.
