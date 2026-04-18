from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth_router, cases_router, executions_router, schedules_router, users_router, folders_router
from app.websocket.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(executions_router)
app.include_router(schedules_router)
app.include_router(users_router)
app.include_router(folders_router)


@app.get("/")
async def root():
    return {"message": "Chaos Platform API", "version": settings.APP_VERSION}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws/logs/{execution_id}")
async def websocket_logs(websocket: WebSocket, execution_id: int):
    await manager.connect(websocket, execution_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, execution_id)
