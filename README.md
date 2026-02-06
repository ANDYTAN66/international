# 实时国际资讯网站（高风险全文版）

该项目为一个可部署的全栈骨架，支持：
- 多来源实时采集（Google News / CNN / Reuters / BBC / AP）
- 新闻卡片显示 `来源 + 发布时间`
- 点击标题进入详情页查看站内全文
- 英文/中文切换
- 中国相关专栏（China Focus）
- 关键词搜索 + 国家筛选 + 主题筛选
- 来源健康监控（up/degraded/down）
- 失败重试队列（源抓取失败、正文提取失败自动重试）
- WebSocket 实时刷新

## 风险说明

你明确选择了高风险路线：该实现会尝试抓取并站内展示全文。  
对于 Reuters/CNN 等来源，这通常涉及版权或服务条款风险，生产环境请自行承担合规责任。

## 技术栈

- 前端：Next.js + Tailwind + Framer Motion
- 后端：FastAPI + APScheduler
- 数据：PostgreSQL
- 部署：Vercel（前端）+ Railway（后端）

## 目录结构

- `backend/`：采集、重试、分类、API、WebSocket
- `frontend/`：界面、筛选控件、详情页、健康监控面板

## 本地运行

### 1) 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) 前端

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

- 前端默认：`http://localhost:3000`
- 后端默认：`http://localhost:8000`

## 必要环境变量

后端（`backend/.env`）：
- `DATABASE_URL`
- `POLL_SECONDS=60`
- `REQUEST_TIMEOUT_SECONDS=20`
- `MAX_ARTICLES_PER_SOURCE=30`
- `FEED_MAX_RETRIES=2`
- `FEED_RETRY_BACKOFF_SECONDS=1.5`
- `RETRY_QUEUE_BATCH_SIZE=20`
- `RETRY_MAX_ATTEMPTS=5`
- `RETRY_INITIAL_DELAY_SECONDS=120`
- `ENABLE_TRANSLATION=true`

前端（`frontend/.env.local`）：
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

## API

- `GET /health`
- `GET /api/news?lang=en|zh&china_only=false&q=&country=&topic=&limit=30&offset=0`
- `GET /api/news/{article_id}?lang=en|zh`
- `GET /api/sources/health`
- `GET /api/retry/metrics`
- `GET /api/filters`
- `WS /ws/news`

## 部署清单（Vercel + Railway）

### A. Railway 部署后端

1. 在 Railway 新建项目并连接此仓库。
2. `Root Directory` 设为仓库根目录，服务启动目录使用 `backend`。
3. 新增 PostgreSQL（Railway 插件或外部 Neon）。
4. 配置后端环境变量（见上文）。
5. `Start Command`：

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. 部署后访问：`https://<railway-domain>/health`，返回 `{"status":"ok"}`。

### B. Vercel 部署前端

1. 在 Vercel 导入同一仓库。
2. `Root Directory` 设为 `frontend`。
3. 配置环境变量：
   - `NEXT_PUBLIC_API_BASE_URL=https://<railway-domain>`
4. 部署并访问首页。

### C. 联调验证

1. 首页能看到新闻卡片（来源+时间）。
2. 点标题能进详情页并看到正文。
3. 切换 `English/中文` 正常。
4. `China Focus` 专栏有数据。
5. 搜索、国家、主题筛选生效。
6. 来源健康面板有状态。
7. 每 1 分钟左右有新内容自动刷新（或收到 WebSocket 推送）。

## 备注

- 如果你是在旧数据库上升级，新增字段/表不会自动迁移；请使用新库或自行做 SQL 迁移。
