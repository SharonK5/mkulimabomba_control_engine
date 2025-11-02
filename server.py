import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# 🔑 Load environment variables from .env file
load_dotenv()

# Optional: Validate critical environment variables
required_vars = ["SECRET_KEY", "DATABASE_URL", "ALGORITHM"]
for var in required_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"❌ Missing required environment variable: {var}")

# Placeholder database functions (to be replaced later with real DB logic)
def get_db():
    yield None

def init_db():
    pass  # Do nothing for now

# Configure app metadata from .env (fallback to defaults if missing)
app_title = os.getenv("APP_NAME", "MkulimaBomba Control Engine")
debug_mode = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

app = FastAPI(
    title=app_title,
    description="AI-powered agricultural decision support system",
    version="2.0.0",
    debug=debug_mode
)

@app.on_event("startup")
async def startup_event():
    print(f"🚀 Starting {app_title} (DEBUG={debug_mode})")
    init_db()

@app.get("/")
async def root():
    return {"message": f"{app_title} API - Healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "control_engine",
        "debug": debug_mode
    }

@app.get("/analytics/popular-queries")
async def get_popular_queries(db: Session = Depends(get_db)):
    return {"popular_queries": ["fertilizer for maize", "pest control", "planting season"]}

@app.get("/analytics/region-stats")
async def get_region_stats(db: Session = Depends(get_db)):
    return {"regions": {"Central": 45, "Rift Valley": 38, "Eastern": 27}}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
