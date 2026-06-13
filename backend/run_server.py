import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from app import app

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=False,
        use_reloader=False,
    )
