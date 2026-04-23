from fastapi import FastAPI, HTTPException
from db.supabase_client import supabase
from routers.upload import router as upload_router

app = FastAPI(title="Retail Offers API")

app.include_router(upload_router)


@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test-db")
def test_db():
    try:
        result = supabase.table("uploads").select("id").limit(1).execute()
        return {
            "success": True,
            "message": "Connected to Supabase successfully",
            "data": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))