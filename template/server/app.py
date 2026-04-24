"""FastAPI app 工厂。"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from template import __version__
from template.server.agent import Agent
from template.server.controller import (
    admin_router,
    dataplane_router,
    register_exception_handlers,
)
from template.server.database.session import dispose_db, init_db

_log = logging.getLogger("template.server.app")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    _log.info("starting template v%s (init db + agent)", __version__)
    await init_db()
    agent = Agent.install()  # 默认 model=None → fallback MockModel
    _log.info("startup complete (agent.model=%s)", agent.model.name)
    try:
        yield
    finally:
        _log.info("shutdown: disposing db + resetting agent")
        Agent.uninstall()
        await dispose_db()
        _log.info("shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="template",
        version=__version__,
        description="template 本地智能体 server(admin + data plane)",
        lifespan=lifespan,
    )
    # Tauri webview 的 origin 是 `https://tauri.localhost`(Win)/ `tauri://localhost`(mac),
    # 与 server 的 `http://127.0.0.1:<port>` 跨 origin 会触发 preflight。server 只绑
    # localhost,外网打不到,allow_origins=["*"] 不引入攻击面。不用 credentials 所以 "*" 合法。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(admin_router, prefix="/admin")
    app.include_router(dataplane_router)
    return app
