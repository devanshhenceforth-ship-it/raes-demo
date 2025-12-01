from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.db import connection
from src.routers import clients, routes_inspection, sse_inspection, inventory
from src.core.config import settings

app = FastAPI(title=settings.APP_NAME)

@app.on_event("startup")
async def startup_event():
    await connection.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await connection.close()

app.include_router(clients.router, prefix=settings.API_PREFIX)
app.include_router(routes_inspection.router, prefix=settings.API_PREFIX)
app.include_router(sse_inspection.router, prefix=settings.API_PREFIX)
app.include_router(inventory.router, prefix=settings.API_PREFIX)
# app.include_router(routes_yolo.router, prefix=settings.API_PREFIX)

# app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
