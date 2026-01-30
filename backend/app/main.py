from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import telemetry
from app.services.websocket import sio
import socketio

# Initialize FastAPI regular app
fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In prod, specify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(telemetry.router, prefix=settings.API_V1_STR, tags=["telemetry"])

@fastapi_app.get("/")
def root():
    return {"message": "Prahari-AI Sentinel Backend Online"}

# Wrap with Socket.IO
# checking if this works with the "app:app" string in uvicorn
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
