# 这是一个项目模板

Python + FastAPI + SQLite + CLI + React + Tauri 的全栈脚手架。克隆下来,跑一条命令就能开一个新项目。

## 怎么用

### 1. 克隆模板

```bash
git clone https://github.com/cliffordll/template.git my-new-app
cd my-new-app
```

### 2. 跑 `new` 命令生成新项目

```bash
python scripts/template.py new my-new-app
```

可选参数:
- `--dir <path>`:指定生成位置(默认**就地改写**当前目录)
- 否则脚本会在**当前目录原地**把所有 `template`/`Template`/`TEMPLATE` 标识符替换成 `my-new-app`/`MyNewApp`/`MY_NEW_APP`(按 `--case-map` 规则),重命名包目录和 spec 文件,并重置 git

### 3. 后续准备

- 装依赖:`uv sync && bun install`
- 换 logo:替换 `assets/logo.svg` → 按 [`assets/logo-design.md`](assets/logo-design.md) §5 的脚本重生成 icons
- 开工:按 [`docs/guides/first-run.md`](docs/guides/first-run.md) 起 server / CLI / Tauri

---

## 模板给你的东西

### 骨架(这些是基础设施,一般不动)

| 位置 | 作用 |
|---|---|
| `template/server/app.py` | FastAPI app 工厂 + lifespan 管理 |
| `template/server/runtime/` | `endpoint.json` / PID lockfile / 优雅启停 |
| `template/server/database/` | SQLite + SQLAlchemy 2.x async + migrations |
| `template/server/controller/` | HTTP 路由分组 + 异常映射 |
| `template/cli/__main__.py` | Typer 入口 + 子命令注册模式 |
| `template/cli/commands/{start,stop,status,logs,stats}.py` | 运维类命令 |
| `template/sdk/client.py` | HTTP 客户端(admin + data plane) |
| `template/sdk/discover.py` | 本机 server 发现 / 自动 spawn |
| `packages/app/` | React + Vite + Tailwind + shadcn UI |
| `packages/desktop/` | Tauri 2.x 桌面壳 + sidecar 绑定 |
| `build/` + `scripts/build.py` + `scripts/publish.py` | PyInstaller 单 exe 打包 + 发布工具 |
| `.github/workflows/` | CI(ruff + pyright + pytest) + release |
| `docs/guides/` | 常用操作手册(首次启动、tauri icons、uv、rust 等) |

### 示例业务(这些是填充物,你可以删 / 改 / 扩)

| 位置 | 作用 | 模板建议 |
|---|---|---|
| `template/server/agent.py` + `template/server/model/` | Controller → Agent → Model 三层(示例给的是 chariot 的 "智能体 + MockModel") | 改 / 删;你的业务对象放这里 |
| `template/server/controller/dataplane.py` | /v1/messages / /v1/chat/completions / /v1/responses 三端点(按 chariot 协议来的) | 换成你自己的业务 endpoint |
| `template/cli/commands/chat.py` + `template/cli/core/` | `template chat` CLI + REPL | 如果你的项目有"主操作",挪用这个结构 |
| `packages/app/src/pages/{Chat,Dashboard,Logs}.tsx` | UI 三页示例 | Dashboard + Logs 通常可以留,Chat 按你的业务改 |
| `tests/server/test_{agent,dataplane,model_mock}.py` | 业务层测试 | 跟着业务代码改 |

### 中间的公共抽象(基础设施还是业务?)

| 位置 | 说明 |
|---|---|
| `template/server/controller/{logs,stats,runtime}.py` | 管理面 endpoint,跟 `LogEntry` 表耦合 |
| `template/server/repository/log.py` + `template/server/service/log_writer.py` | 请求流水落库;通用,几乎都保留 |
| `template/server/database/migrations/001_init.sql` | 只建 `logs` 表。如果你的项目不记请求流水,也可以整个删掉 |

---

## 分层契约

模板遵循的窄接口设计:

```
HTTP Controller  →  业务层(你实现)  →  infra(DB / HTTP client / 等)
```

- Controller 只管 HTTP 协议,不懂业务
- 业务层只暴露窄接口给 Controller,不懂 HTTP
- infra 不懂业务

详见 [`docs/DESIGN.md`](docs/DESIGN.md)。

---

## 进一步

- [`docs/guides/first-run.md`](docs/guides/first-run.md) —— 首次启动 checklist
- [`CLAUDE.md`](CLAUDE.md) —— 协作约定(Git gate / 静态检查 / 分层规则),新项目可以沿用
- 模板源仓库:<https://github.com/cliffordll/template.git>
- 使用了模板的参考项目:<https://github.com/cliffordll/chariot.git>(智能体 server)
