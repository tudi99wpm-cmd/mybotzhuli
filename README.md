# Recursive Self-Improving AI Agent

一个可部署到 GitHub 和云服务器的最小可运行 AI 智能体骨架，包含以下能力：

- `FastAPI` API 服务
- 后台 worker 执行任务
- OpenAI 兼容大模型调用
- `Redis` 任务队列与 `PostgreSQL` 持久化
- 基于失败样本的自改进与 PR 草案骨架
- `PostgreSQL`、`Redis`、`Docker Compose`
- `GitHub Actions` 持续集成与定时自进化工作流

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

1. 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --break-system-packages -r requirements.txt
```

2. 复制环境变量

```bash
cp .env.example .env
```

然后填写：

- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `MODEL_NAME`
- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`

3. 启动 API

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

4. 启动 worker

```bash
python -m apps.worker.main
```

5. 运行测试

```bash
python3 -m pytest
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
