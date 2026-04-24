# Template

> **Python + FastAPI + SQLite + CLI + React + Tauri 全栈脚手架**。克隆它,一条命令生成新项目,直接开工。

## 开一个新项目

```bash
git clone https://github.com/cliffordll/template.git my-new-app
cd my-new-app
python scripts/template.py new my-new-app
```

`template.py new` 会把所有 `template` / `Template` / `TEMPLATE` 标识符换成你提供的名字(含大小写变体)、重命名 Python 包目录、rename spec 文件、重置 git。

完整模板使用说明 → [`TEMPLATE.md`](TEMPLATE.md)

## 模板里有什么

- **后端骨架**:FastAPI app + lifespan + SQLite + migration + 请求流水 logs
- **CLI 骨架**:Typer 入口 + 子命令注册 + start/stop/status/logs/stats + REPL 示例(chat)
- **SDK 骨架**:httpx 客户端 + server 发现/自动 spawn
- **前端骨架**:React + Vite + Tailwind + shadcn/ui + Dashboard/Logs/Chat 三页
- **桌面壳**:Tauri 2.x + PyInstaller sidecar 绑定 + single-instance 插件
- **发布链路**:`scripts/publish.py` 统一 bump / build / tag + GitHub Release Action
- **CI**:ruff / pyright / pytest
- **协作约定**:`CLAUDE.md`(Git gate / 分层规则 / 静态检查)

详细骨架清单 vs 示例业务区分 → [`TEMPLATE.md`](TEMPLATE.md) §"模板给你的东西"

## 模板里的"示例业务"

模板附带一个最小智能体示例(Controller → Agent → MockModel 三层),用来演示如何在骨架上挂业务。你可以:

- **保留参考**:按示例在 `template/server/agent.py` + `template/server/model/` 改成你的业务对象
- **替换**:删掉 agent/model 层,直接在 `controller/dataplane.py` 接你的逻辑
- **完整扩展版参考**:<https://github.com/cliffordll/chariot.git>

## Quick start(本模板本身,不经 template.py new)

```bash
uv sync && bun install

# CLI / server
uv run python -m template.server            # 终端 A
uv run template chat "hello"                # 终端 B

# Tauri 桌面壳(首次 sidecar 必须打)
uv run --group build python scripts/build.py --target server --sync-sidecar
bun run --filter=@template/desktop tauri dev

# Web 前端(纯浏览器)
uv run python -m template.server
bun run --filter=@template/app dev
```

完整首次启动流程 → [`docs/guides/first-run.md`](docs/guides/first-run.md)

## 技术栈

| Layer | Choice |
|---|---|
| Backend | Python 3.12+ · FastAPI · SQLAlchemy 2.x async · aiosqlite · Typer |
| Frontend | React · TypeScript · Vite · Tailwind · shadcn/ui |
| Desktop shell | Tauri 2.x (Rust) |
| Package managers | uv (Python) · bun (frontend / Tauri workspace) |
| Packaging | PyInstaller single exe (as Tauri sidecar) |

## 文档

| File | Purpose |
|---|---|
| [`TEMPLATE.md`](TEMPLATE.md) | **模板使用说明** — 如何派生新项目、骨架 vs 示例清单 |
| [`docs/DESIGN.md`](docs/DESIGN.md) | 架构契约 — 层与层之间的窄接口 |
| [`docs/FEATURE.md`](docs/FEATURE.md) | 任务清单(示例业务的阶段记录,新项目清空重写) |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 长期方向(示例,新项目清空重写) |
| [`docs/guides/first-run.md`](docs/guides/first-run.md) | 首次启动 checklist |
| [`docs/guides/`](docs/guides/) | 各子工具操作手册(Typer / DB / Tauri / uv / Rust) |
| [`CLAUDE.md`](CLAUDE.md) | Claude 协作约定 — Git gate / 静态检查 / 分层规则 |
