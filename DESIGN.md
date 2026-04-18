# Chaos Platform 设计文档

## 1. 系统概述

### 1.1 项目背景

Chaos Platform 是一个基于 Web 的混沌工程管理平台，旨在将现有的命令行混沌工程工具（chaos_oop_design）转换为可视化的 Web 管理平台，提供更友好的用户体验和更高效的团队协作能力。

### 1.2 目标用户

- 中等规模团队（10-50人）
- 需要角色权限管理（管理员/普通用户/只读用户）
- 需要多人协作执行混沌工程测试

### 1.3 核心功能

| 功能模块 | 描述 |
|---------|------|
| 用例管理 | 创建、编辑、删除、导入 YAML 用例，支持目录和标签分类 |
| 执行中心 | 立即执行用例，实时查看执行日志和状态 |
| 执行记录 | 查看历史执行记录，导出报告（HTML/PDF/Excel） |
| 定时任务 | 配置 Cron 定时执行用例 |
| 用户管理 | 用户注册、角色管理、权限控制 |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                               │
│                    http://localhost:8080                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx (Frontend Container)                  │
│  ┌─────────────────┐    ┌─────────────────────────────────┐     │
│  │   静态资源       │    │   反向代理 /api → backend:8000  │     │
│  │   /dist/*       │    │   反向代理 /ws → backend:8000   │     │
│  └─────────────────┘    └─────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   Backend API     │ │  Celery Worker  │ │   Celery Beat       │
│   (FastAPI)       │ │  (任务执行)      │ │   (定时调度)         │
│   Port: 8000      │ │                 │ │                     │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   PostgreSQL      │ │     Redis       │ │   Chaos Module      │
│   (数据存储)       │ │  (缓存/队列)    │ │   (混沌工程核心)     │
│   Port: 5432      │ │   Port: 6379    │ │                     │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
```

### 2.2 技术选型

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| 前端框架 | Vue 3 + TypeScript | 现代化响应式框架，类型安全 |
| UI 组件库 | Element Plus | 成熟的企业级组件库，中文支持好 |
| 代码编辑器 | Monaco Editor | VS Code 同款编辑器，YAML 语法高亮 |
| 后端框架 | FastAPI | 高性能异步框架，自动生成 API 文档 |
| ORM | SQLAlchemy 2.0 | 成熟的 Python ORM，支持异步 |
| 任务队列 | Celery | 成熟的分布式任务队列 |
| 数据库 | PostgreSQL 15 | 稳定可靠的关系型数据库 |
| 缓存 | Redis 7 | 高性能缓存和消息代理 |
| 容器化 | Docker Compose | 简化部署和运维 |

---

## 3. 数据库设计

### 3.1 ER 图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │    Case     │       │    Tag      │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │──┐    │ id          │──┐    │ id          │
│ username    │  │    │ name        │  │    │ name        │
│ password_hash│  │    │ description │  │    │ color       │
│ role        │  │    │ yaml_content│  │    └─────────────┘
│ email       │  │    │ folder      │  │           │
│ is_active   │  │    │ is_template │  │           │
└─────────────┘  │    │ creator_id  │◄─┘           │
      │          │    └─────────────┘              │
      │          │          │                      │
      │          │          │      ┌───────────────┘
      │          │          │      │
      │          │          ▼      ▼
      │          │    ┌─────────────────┐
      │          │    │    CaseTag      │
      │          │    ├─────────────────┤
      │          │    │ case_id         │
      │          │    │ tag_id          │
      │          │    └─────────────────┘
      │          │
      │          │
      │          ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Execution  │       │ ExecutionLog│       │  Schedule   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │──┐    │ id          │       │ id          │
│ case_id     │◄─┼───►│ execution_id│       │ name        │
│ executor_id │◄─┘    │ level       │       │ case_id     │
│ status      │       │ message     │       │ cron_expr   │
│ start_time  │       │ timestamp   │       │ creator_id  │
│ end_time    │       └─────────────┘       │ is_active   │
│ duration    │                             │ next_run    │
│ result      │                             │ last_run    │
│ error_message│                            └─────────────┘
└─────────────┘
```

### 3.2 表结构详解

#### 3.2.1 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(50) | 用户名，唯一 |
| password_hash | String(255) | 密码哈希 |
| role | String(20) | 角色：admin/user/readonly |
| email | String(100) | 邮箱，唯一 |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 3.2.2 用例表 (cases)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(200) | 用例名称 |
| description | Text | 描述 |
| yaml_content | Text | YAML 内容 |
| file_path | String(500) | 原始文件路径 |
| case_type | String(50) | 类型：case/workflow |
| folder | String(200) | 所属目录 |
| is_template | Boolean | 是否模板 |
| creator_id | Integer | 创建者 ID |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 3.2.3 执行记录表 (executions)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| case_id | Integer | 用例 ID |
| executor_id | Integer | 执行者 ID |
| status | String(20) | 状态：pending/running/success/failed/cancelled/timeout |
| start_time | DateTime | 开始时间 |
| end_time | DateTime | 结束时间 |
| duration | Float | 执行时长（秒） |
| result | JSON | 执行结果 |
| error_message | Text | 错误信息 |
| report_path | String(500) | 报告路径 |
| log_file_path | String(500) | 日志文件路径 |
| created_at | DateTime | 创建时间 |

#### 3.2.4 执行日志表 (execution_logs)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| execution_id | Integer | 执行记录 ID |
| level | String(10) | 日志级别：INFO/WARNING/ERROR |
| message | Text | 日志内容 |
| timestamp | DateTime | 时间戳 |

#### 3.2.5 定时任务表 (schedules)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(200) | 任务名称 |
| case_id | Integer | 用例 ID |
| cron_expr | String(100) | Cron 表达式 |
| creator_id | Integer | 创建者 ID |
| is_active | Boolean | 是否激活 |
| next_run | DateTime | 下次执行时间 |
| last_run | DateTime | 上次执行时间 |
| last_status | String(20) | 上次执行状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

## 4. API 设计

### 4.1 API 概览

| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| 认证 | /api/auth | 登录、登出、获取当前用户 |
| 用例 | /api/cases | 用例 CRUD、验证、导入 |
| 执行 | /api/executions | 执行用例、查看记录 |
| 定时任务 | /api/schedules | 定时任务管理 |
| 用户 | /api/users | 用户管理（管理员） |
| WebSocket | /ws/logs/{id} | 实时日志推送 |

### 4.2 认证 API

```
POST   /api/auth/login     # 登录，返回 JWT Token
POST   /api/auth/logout    # 登出
GET    /api/auth/me        # 获取当前用户信息
```

### 4.3 用例 API

```
GET    /api/cases              # 获取用例列表（分页、筛选）
POST   /api/cases              # 创建用例
GET    /api/cases/{id}         # 获取用例详情
PUT    /api/cases/{id}         # 更新用例
DELETE /api/cases/{id}         # 删除用例
POST   /api/cases/validate     # 验证 YAML 格式
POST   /api/cases/import       # 导入 YAML 文件
GET    /api/cases/folders      # 获取目录列表
GET    /api/cases/tags         # 获取标签列表
POST   /api/cases/tags         # 创建标签
```

### 4.4 执行 API

```
GET    /api/executions             # 获取执行记录列表
POST   /api/executions             # 执行用例
GET    /api/executions/{id}        # 获取执行详情
DELETE /api/executions/{id}        # 删除执行记录
DELETE /api/executions             # 批量删除执行记录
GET    /api/executions/{id}/report # 导出报告
```

### 4.5 定时任务 API

```
GET    /api/schedules              # 获取定时任务列表
POST   /api/schedules              # 创建定时任务
GET    /api/schedules/{id}         # 获取定时任务详情
PUT    /api/schedules/{id}         # 更新定时任务
DELETE /api/schedules/{id}         # 删除定时任务
PUT    /api/schedules/{id}/toggle  # 启用/禁用定时任务
```

### 4.6 用户 API

```
GET    /api/users              # 获取用户列表（管理员）
POST   /api/users              # 创建用户（管理员）
GET    /api/users/{id}         # 获取用户详情
PUT    /api/users/{id}         # 更新用户（管理员）
DELETE /api/users/{id}         # 删除用户（管理员）
```

---

## 5. 前端设计

### 5.1 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Logo + 导航菜单 + 用户信息                          │
├─────────────────────────────────────────────────────────────┤
│        │                                                    │
│  Side  │              Main Content                          │
│  Bar   │                                                    │
│        │   ┌─────────────────────────────────────────────┐  │
│  - 首页│   │                                             │  │
│  - 用例│   │              页面内容                        │  │
│  - 执行│   │                                             │  │
│  - 定时│   │                                             │  │
│  - 用户│   │                                             │  │
│        │   └─────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Footer: 版权信息                                           │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 页面列表

| 路由 | 页面 | 说明 |
|------|------|------|
| /login | Login | 登录页 |
| /dashboard | Dashboard | 首页仪表盘 |
| /cases | CaseList | 用例列表 |
| /cases/create | CaseEdit | 创建用例 |
| /cases/:id/edit | CaseEdit | 编辑用例 |
| /executions | ExecutionList | 执行记录列表 |
| /executions/:id | ExecutionDetail | 执行详情（实时日志） |
| /schedules | ScheduleList | 定时任务列表 |
| /users | UserList | 用户管理（管理员） |

### 5.3 状态管理 (Pinia Stores)

| Store | 说明 |
|-------|------|
| auth | 用户认证状态、Token 管理 |
| cases | 用例列表缓存 |
| executions | 执行记录缓存 |

---

## 6. 任务执行流程

### 6.1 立即执行流程

```
用户点击执行
    │
    ▼
前端 POST /api/executions
    │
    ▼
后端创建 Execution 记录 (status=pending)
    │
    ▼
后端发送任务到 Celery Queue
    │
    ▼
返回 execution_id 给前端
    │
    ▼
前端建立 WebSocket 连接 /ws/logs/{id}
    │
    ▼
Celery Worker 执行任务
    │
    ├──► 更新 status=running
    │
    ├──► 发送日志到 WebSocket
    │
    ├──► 执行 chaos 模块
    │
    ├──► 更新 status=success/failed
    │
    ▼
前端显示最终结果
```

### 6.2 定时执行流程

```
Celery Beat (每60秒)
    │
    ▼
检查 schedules 表 (is_active=true, next_run <= now)
    │
    ▼
为每个匹配的 schedule 创建执行任务
    │
    ▼
更新 schedule.next_run (根据 cron 表达式)
    │
    ▼
Celery Worker 执行任务（同立即执行流程）
```

---

## 7. 安全设计

### 7.1 认证机制

- 使用 JWT Token 进行身份认证
- Token 有效期：24 小时
- Token 存储在 localStorage

### 7.2 权限控制

| 角色 | 权限 |
|------|------|
| admin | 所有操作，包括用户管理 |
| user | 创建/编辑/删除用例，执行用例，管理自己的定时任务 |
| readonly | 仅查看用例和执行记录 |

### 7.3 安全措施

- 密码使用 bcrypt 加密存储
- API 请求需要 Token 验证
- 敏感操作需要管理员权限
- SQL 注入防护（ORM）
- XSS 防护（Vue 自动转义）

---

## 8. 部署架构

### 8.1 Docker Compose 服务

```yaml
services:
  postgres:      # PostgreSQL 数据库
  redis:         # Redis 缓存/队列
  backend:       # FastAPI 后端
  celery_worker: # Celery 任务执行器
  celery_beat:   # Celery 定时调度器
  frontend:      # Nginx + Vue 前端
```

### 8.2 网络配置

所有服务在同一个 Docker 网络 (chaos_network) 中，通过服务名互相访问。

### 8.3 数据持久化

| 卷 | 说明 |
|----|------|
| postgres_data | 数据库数据 |
| redis_data | Redis 数据 |
| ./logs | 执行日志文件 |
| ./reports | 导出报告文件 |
| ./chaos | 混沌工程模块（只读挂载） |

---

## 9. 扩展性设计

### 9.1 水平扩展

- Celery Worker 可以部署多个实例
- 后端 API 可以部署多个实例（需要负载均衡）
- Redis 可以配置集群模式
- PostgreSQL 可以配置主从复制

### 9.2 功能扩展点

- 支持更多报告格式
- 集成告警通知（邮件、钉钉、企业微信）
- 支持用例版本控制
- 支持用例审批流程
- 支持执行结果对比分析

---

## 10. 监控与日志

### 10.1 日志收集

- 后端日志：stdout（可通过 docker logs 查看）
- 执行日志：数据库 + 文件系统
- Celery 日志：stdout

### 10.2 健康检查

- PostgreSQL: pg_isready
- Redis: redis-cli ping
- Backend: /health 端点

---

## 11. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-04-17 | 初始版本，完成核心功能 |
