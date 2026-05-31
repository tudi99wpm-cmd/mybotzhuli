import uvicorn
from apps.api.main import app

if __name__ == "__main__":
    print("🚀 Starting FastAPI Service natively on Windows via Standalone EXE...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
