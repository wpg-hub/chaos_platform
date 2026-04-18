# Chaos Platform - 混沌工程管理平台

一个基于 Web 的混沌工程管理平台，提供用例管理、执行调度、历史记录、定时任务等功能。

## 功能特性

- **用例管理**: 创建、编辑、删除用例，支持 YAML 编辑器、目录分类、标签管理
- **执行管理**: 立即执行、实时日志流、执行状态监控
- **历史记录**: 执行历史查看、报告导出（HTML/PDF/Excel）
- **定时任务**: Cron 表达式配置定时执行
- **用户管理**: 多角色权限控制（管理员/普通用户/只读用户）
- **实时日志**: WebSocket 实时推送执行日志

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + Monaco Editor |
| 后端 | FastAPI + SQLAlchemy 2.0 + Celery |
| 数据库 | PostgreSQL 15 |
| 缓存/队列 | Redis 7 |
| 容器化 | Docker + Docker Compose |

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+

### 1. 启动服务

```bash
cd /home/gsta/chaos_platform
sudo docker compose up -d
```

### 2. 创建管理员用户

```bash
sudo docker compose exec backend python -m app.init_db
```

### 3. 访问平台

打开浏览器访问: http://localhost:8080

**默认账号:**
- 用户名: `admin`
- 密码: `admin123`

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 8080 | Web 界面 |
| backend | 8000 | API 服务 |
| postgres | 5432 | 数据库 |
| redis | 6379 | 缓存/消息队列 |

## 项目结构

```
chaos_platform/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── auth.py        # 认证接口
│   │   │   ├── cases.py       # 用例管理
│   │   │   ├── executions.py  # 执行管理
│   │   │   ├── schedules.py   # 定时任务
│   │   │   └── users.py       # 用户管理
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   └── security.py    # 安全认证
│   │   ├── tasks/             # Celery 任务
│   │   │   └── execution_task.py
│   │   ├── websocket/         # WebSocket 管理
│   │   └── schemas.py         # Pydantic 模型
│   └── requirements.txt
│
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── api/               # API 调用
│   │   ├── components/        # 公共组件
│   │   ├── views/             # 页面组件
│   │   │   ├── Dashboard.vue  # 首页仪表盘
│   │   │   ├── CaseList.vue   # 用例列表
│   │   │   ├── ExecutionDetail.vue # 执行详情
│   │   │   └── ...
│   │   ├── stores/            # Pinia 状态管理
│   │   └── router/            # Vue Router
│   └── package.json
│
├── chaos/                      # 混沌工程核心模块
├── docker/                     # Docker 配置
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── logs/                       # 日志目录
├── reports/                    # 报告目录
├── cases/                      # 用例文件目录
├── config.yaml                 # 混沌工程配置
├── docker-compose.yml
├── README.md
└── DESIGN.md                   # 设计文档
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 常用命令

```bash
# 查看服务状态
sudo docker compose ps

# 查看日志
sudo docker compose logs -f backend
sudo docker compose logs -f celery_worker

# 重启服务
sudo docker compose restart

# 停止服务
sudo docker compose down

# 重建服务
sudo docker compose up -d --build
```

## 开发指南

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 许可证

MIT License
# chaos_platform
