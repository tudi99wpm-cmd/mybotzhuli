# Recursive Self-Improving AI Agent (Windows Standalone EXE & Cross-Platform)

一个**开箱即用、可直接双击运行的 Windows 独立可执行程序 (.exe) 版**与跨平台自改进 AI 智能体骨架。它既能在 Windows 本地提供秒级启动的双击运行体验，也能无缝部署到 GitHub Actions 定时流与云服务器。

### 🌟 核心特性：
- **💻 Windows 极速双击版 (Standalone EXE)**：专为 Windows 平台预编译打包，无需配置任何 Python 环境、Postgres 数据库或 Redis 队列，双击即用。
- **🔌 零依赖单机运行模式**：采用本地文件系统作为存储，极速内存队列作为任务通道，实现免装数据库运行。
- **🚀 完整异步架构**：基于 `FastAPI` 构建 API 服务，后台独立 `Worker` 处理耗时 AI 智能体任务。
- **🤖 闭环自改进/自进化**：AI 智能体自动记录失败样本，并根据失败样本自我生成优化代码与 PR 分支。
- **☁️ 云端与跨平台无缝兼容**：保留完整的 `Docker Compose`、`GitHub Actions` 持续集成与云端定时部署能力。

## 项目结构

```text
apps/
  api/
  worker/
packages/
  agent_core/
  evals/
tests/
.github/workflows/
```

## 本地开发

### Option A: Windows 独立 EXE 极速部署运行 (免 Python / 免 Postgres / 免 Redis)

本项目已为 Windows 平台深度适配并提供了**预编译的 Standalone EXE 运行版**。您可以在完全不需要配置 Python 环境、PostgreSQL 和 Redis 数据库的情况下，直接双击启动完整的 API 和 Worker 架构！

1. **配置环境变量**：
   将项目根目录下的 `.env.example` 复制一份并重命名为 `.env`。
   项目默认已被配置为**零依赖单机运行模式**：
   ```ini
   STORE_BACKEND=file    # 任务状态自动存储在本地 artifacts 目录下，免去 PostgreSQL
   QUEUE_BACKEND=memory  # 后台任务使用极速内存队列，免去 Redis
   ```
   只需在 `.env` 中填写您的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `MODEL_NAME` 即可开始使用。

2. **极速 1-Click 一键双击启动**：
   双击运行根目录下的 **`run_all_win.ps1`**（以 PowerShell 运行），它会自动以并发方式为您同时拉起并运行 API 和 Worker 的 EXE 服务。

3. **分步双击运行**：
   - 启动 API 接口服务：双击运行 **`dist/mybotzhuli_api.exe`** (运行在 `http://127.0.0.1:8000`)
   - 启动 Worker 任务服务：双击运行 **`dist/mybotzhuli_worker.exe`**

4. **重新打包 EXE 编译**：
   如果您对 Python 代码进行了任何修改，只需在 Windows 下使用 PowerShell 运行以下命令，即可一键在 `dist/` 目录下重新生成最新的 Windows 独立 EXE：
   ```powershell
   powershell -ExecutionPolicy Bypass -File build_exe.ps1
   ```

---

### Option B: 跨平台 Python 命令行开发 (Linux/macOS/Windows)

1. **一键 Windows 初始化环境**（Windows 用户推荐）：
   根目录下提供了 **`setup_win.ps1`** 脚本。右键使用 PowerShell 运行该脚本，它会自动探测您本机的 Python 3.12 虚拟环境，自动进行环境清理并 100% 成功安装所有依赖，同时为您初始化好单机模式下的 `.env` 配置文件。

2. **手动创建虚拟环境并安装依赖**：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **复制并填写环境变量**：

```bash
cp .env.example .env
```

然后填写：
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `MODEL_NAME`
- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`

4. **命令行分步启动服务**：
   - 启动 API：`uvicorn apps.api.main:app --host 0.0.0.0 --port 8000` 或运行 `.\run_api.bat`
   - 启动 Worker：`python -m apps.worker.main` 或运行 `.\run_worker.bat`

5. **运行单元测试**：

```bash
python -m pytest
```

## Docker Compose

```bash
docker compose up --build
```

服务：

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

默认运行方式：

- API 创建任务后会写入 PostgreSQL
- 任务 ID 会进入 Redis 队列
- worker 从 Redis 拉取任务并调用 LLM

## API 示例

创建任务：

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"input":"总结这个仓库的结构"}'
```

查询任务：

```bash
curl http://localhost:8000/tasks/<task_id>
```

触发自改进扫描：

```bash
curl -X POST http://localhost:8000/self-improve/run
```

## GitHub 部署建议

1. 新建 GitHub 仓库并推送代码
2. 在仓库 `Settings -> Secrets and variables -> Actions` 中配置：
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `MODEL_NAME`
   - `DEPLOY_HOST`
   - `DEPLOY_USER`
   - `DEPLOY_SSH_KEY`
3. 根据你的云主机修改 `.github/workflows/deploy.yml`
4. 在服务器执行 `docker compose up -d --build`

## 自进化流程

1. API 或 worker 记录失败样本
2. 定时任务读取失败样本并生成改进建议
3. 改进任务输出到 `artifacts/self_improve_report.json`
4. 如果配置了 `GITHUB_TOKEN` 与 `GITHUB_REPOSITORY`，系统会同步生成 PR 草案请求
5. 你可以继续把“生成修改代码并提交分支”的步骤接上

当前版本先把基础闭环搭起来，后续可以继续接入：

- GitHub App 自动提 PR
- 向量记忆
- 多智能体协作
- 真实 benchmark 数据集
