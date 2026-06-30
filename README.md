# 四大名著知识问答系统

基于 **FastAPI + React + RAG** 构建的四大名著智能知识问答应用，以检索增强生成（RAG）技术实现精准的文学知识检索与自然语言回答。

---

## 项目概述

本项目是一个前后端分离的全栈应用，覆盖《红楼梦》《西游记》《水浒传》《三国演义》四大名著的原文数据。系统预先将原文内容和问答对进行文本切片、向量化后存入 Milvus 向量数据库；用户提问时，通过**混合检索**（向量语义检索 + 关键词精确匹配）召回相关内容，再由 DeepSeek 大语言模型生成专业、流畅的回答。

### 核心功能

| 功能 | 说明 |
|------|------|
| 用户认证 | JWT 注册/登录，Bearer Token 鉴权 |
| 四大名著问答 | 基于 RAG 的智能知识问答，覆盖四部名著的人物、情节、诗词等 |
| 混合检索 | 稠密向量语义检索 + 稀疏关键词检索，兼顾语义理解和精确匹配 |
| API 文档 | 自动生成的 Swagger UI 交互式文档 |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React 18)                          │
│  Login → SelectMode → FourClassicQA                              │
│  HashRouter · AuthContext · ProtectedRoute · CSS                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP (JSON + Bearer Token)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       后端 (FastAPI)                             │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────────────────────┐   │
│  │  Auth 模块        │    │  RAG 问答模块 (fgcnrag)          │   │
│  │  /api/v1/auth/*   │    │  /fgcn/chat                     │   │
│  │  JWT + bcrypt     │    │  DeepSeek LLM                   │   │
│  │  MySQL (users)    │    │  混合检索 → Prompt → 生成       │   │
│  └──────────────────┘    └──────────────┬───────────────────┘   │
│                                         │                        │
└─────────────────────────────────────────┼────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           ▼                           │
              │  ┌──────────────────────────────────────────────────┐ │
              │  │           Milvus 向量数据库                       │ │
              │  │  Collection: four_classics_knowledge              │ │
              │  │  稠密向量 (1024维) + 稀疏向量 + 文本 + 元数据     │ │
              │  └──────────────────────────────────────────────────┘ │
              │                           ▲                           │
              │  ┌──────────────────────────────────────────────────┐ │
              │  │             数据预处理管线                        │ │
              │  │  原文TXT → 文本切片 → 向量化 → 入库               │ │
              │  │  问答对XLSX → text-embedding-v4 → Milvus          │ │
              │  └──────────────────────────────────────────────────┘ │
              └───────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端框架** | React 18 + TypeScript | SPA 单页应用 |
| **前端路由** | React Router DOM 6 | HashRouter 模式 |
| **构建工具** | Vite 5 | 极速开发与构建 |
| **后端框架** | FastAPI + Uvicorn | 异步高性能 Web 框架 |
| **LLM** | DeepSeek (deepseek-v4-flash) | 大语言模型生成回答 |
| **向量模型** | 阿里百炼 text-embedding-v4 | 1024 维稠密向量 |
| **向量数据库** | Milvus | 混合检索（向量 + 关键词） |
| **关系数据库** | MySQL (PyMySQL) | 用户数据存储 |
| **认证** | python-jose JWT + passlib bcrypt | Token 鉴权 |
| **日志** | Loguru | 结构化日志 |

---

## 目录结构

```
fgcn/
├── main.py                              # FastAPI 后端主入口
├── requirements.txt                     # Python 依赖
├── .env                                 # 环境变量配置（不提交）
├── .env.template                        # 环境变量模板
├── README.md
│
├── backend/                             # 后端认证与数据库模块
│   ├── database/
│   │   └── connection.py                # MySQL 连接管理 + users 表初始化
│   └── auth/
│       ├── router.py                    # 认证接口 (register/login/me)
│       ├── models.py                    # Pydantic 请求/响应模型
│       ├── security.py                  # JWT 创建验证 + bcrypt 密码哈希
│       └── dependencies.py             # get_current_user 依赖注入
│
├── fgcnrag/                             # 四大名著 RAG 模块
│   ├── fgcn/
│   │   ├── api/chat.py                  # 问答 API 接口
│   │   ├── chain/qa_rag.py             # RAG 问答链（检索 + Prompt + LLM）
│   │   ├── retriever/
│   │   │   └── hybrid_retriever.py      # 混合检索器（向量 + 关键词）
│   │   ├── embedder/embedding.py        # 向量化（阿里百炼 API）
│   │   ├── chunker/text_splitter.py     # 文本切片
│   │   ├── loader/
│   │   │   ├── document_loader.py       # TXT 原文加载器
│   │   │   └── excel_loader.py          # XLSX 问答对加载器
│   │   ├── database/vdb_init.py         # Milvus 数据库操作
│   │   ├── config.py                    # RAG 配置（从 .env 读取）
│   │   └── insert_data.py              # 数据预处理与入库脚本
│   └── data/                            # 四大名著原文 + 问答对数据
│       ├── 《红楼梦》.txt
│       ├── 《西游记》.txt
│       ├── 《水浒传》.txt
│       ├── 《三国演义》.txt
│       ├── 红楼梦问答对.xlsx
│       ├── 西游记人物问答对.xlsx
│       ├── 水浒传问答对.xlsx
│       └── 三国演义问答对.xlsx
│
└── frontend/                            # React 前端项目
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── public/picture/                  # 静态图片资源
    └── src/
        ├── main.tsx                     # 入口文件
        ├── App.tsx                      # 根组件（AuthContext + 路由）
        ├── api.ts                       # API 调用封装 + Token 管理
        ├── index.css                    # 全局样式
        └── pages/
            ├── Login.tsx                # 登录/注册页面
            ├── SelectMode.tsx           # 功能模块选择页
            └── FourClassicQA.tsx        # 四大名著问答页
```

---

## 快速开始

### 环境要求

| 软件 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| Node.js | 18+ |
| MySQL | 5.7+ |
| Milvus | 2.4+ (Standalone 或 Docker) |

### 1. 克隆项目

```bash
git clone <repo-url>
cd fgcn
```

### 2. 配置环境变量

复制模板文件并填写实际值：

```bash
cp .env.template .env
```

编辑 `.env`，必填项：

```env
# ========== 必填 ==========
# DeepSeek LLM API（用于生成回答）
DEEPSEEK_API_KEY=sk-your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# 百炼平台 API（用于文本向量化）
BAILIAN_API_KEY=sk-your_bailian_api_key
BAILIAN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1

# JWT 密钥（用于 Token 签发，请设置为随机字符串）
JWT_SECRET_KEY=your_random_secret_key

# MySQL 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_db_password
DB_NAME=fastapi_study

# Milvus 向量数据库
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DB=Four_classic
```

### 3. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 4. 准备向量数据

确保 Milvus 已启动，然后运行数据入库脚本（将四大名著原文和问答对向量化并存入 Milvus）：

```bash
cd fgcnrag/fgcn
python insert_data.py
```

> 首次运行会创建 Milvus Collection 并自动建立索引，约需数分钟。

### 5. 启动后端

```bash
python main.py
```

服务运行在 `http://127.0.0.1:8080`，API 交互文档 `http://127.0.0.1:8080/docs`。

### 6. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`，通过 Vite 代理将 API 请求转发到后端。

---

## API 接口文档

所有接口的请求/响应均为 JSON 格式。完整交互文档见启动后的 `/docs` (Swagger UI)。

### 认证模块

#### 用户注册 `POST /api/v1/auth/register`

```json
// 请求
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "secure_password"
}

// 响应 200
{
  "id": 1,
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "is_active": true
}

// 响应 400 — 用户名已存在
{ "detail": "用户名已存在" }
```

#### 用户登录 `POST /api/v1/auth/login/access-token`

使用 `application/x-www-form-urlencoded` 格式：

```bash
curl -X POST http://127.0.0.1:8080/api/v1/auth/login/access-token \
  -d "username=zhangsan&password=secure_password"
```

```json
// 响应 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

// 响应 400 — 用户名或密码错误
{ "detail": "用户名或密码错误" }

// 响应 403 — 用户被禁用
{ "detail": "用户已被禁用" }
```

#### 获取当前用户 `GET /api/v1/auth/me`

```
Authorization: Bearer <access_token>
```

```json
// 响应 200
{
  "id": 1,
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "is_active": true
}

// 响应 401 — Token 无效或过期
{ "detail": "无效的认证令牌" }
```

### 四大名著问答模块

#### 知识问答 `POST /fgcn/chat`

> **需要认证**：请求头需携带 `Authorization: Bearer <access_token>`

```json
// 请求
{
  "query": "孙悟空为什么被压在五指山下？"
}

// 响应 200
{
  "answer": "孙悟空因大闹天宫，被如来佛祖以五指化作五行山镇压……"
}

// 响应 400 — 问题为空
{ "detail": "问题不能为空" }

// 响应 401 — 未登录
{ "detail": "无效的认证令牌" }
```

---

## 前端页面说明

### 登录/注册页 (`/login`)

- 支持登录和注册切换
- 注册自动登录
- JWT Token 存储在 `localStorage`

### 模式选择页 (`/select`)

- 登录后自动跳转
- 显示用户名和退出按钮
- 卡片式功能入口

### 四大名著问答页 (`/four-classic`)

- 卷轴风格的聊天界面
- 顶部展示四部名著图标
- 支持连续对话
- 发送时携带 Bearer Token 鉴权

### 路由保护

所有功能页面均通过 `ProtectedRoute` 包裹，未登录自动跳转登录页。路由采用 `HashRouter` 模式。

---

## RAG 系统详解

### 数据管线

```
原始数据                   文本切片                  向量化                     存储
───────────────────────────────────────────────────────────────────────────────────
《红楼梦》.txt ──┐
《西游记》.txt ──┤
《水浒传》.txt ──┤  → ChunkSplitter  →  text-embedding-v4  →  Milvus Collection
《三国演义》.txt ──┤     (chunk_size=500,    (1024维稠密向量)     four_classics_knowledge
                │      overlap=100)
问答对.xlsx ────┘
```

### 混合检索策略

系统同时执行两种检索并合并结果：

| 检索方式 | 原理 | 优势 |
|----------|------|------|
| **稠密向量检索** | 问题向量化 → Milvus ANN 近似最近邻搜索 | 理解语义，匹配近义表达 |
| **关键词检索** | SQL LIKE 匹配 text 字段 | 精确匹配人名、地名、专有名词 |

### 问答流程

```
用户提问 → [混合检索: Top-5 相关文档] → [构建 Prompt] → [DeepSeek LLM] → 答案
```

Prompt 设计要点：
- 设定 LLM 为四大名著文学专家角色
- 注入检索到的参考内容
- 要求直接、流畅、无引导词的回答格式
- temperature=0.1，低随机性确保答案稳定

---

## 配置说明

`.env` 文件完整配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（必填） | — |
| `DEEPSEEK_API_BASE` | DeepSeek API 地址 | `https://api.deepseek.com/v1` |
| `BAILIAN_API_KEY` | 阿里百炼 API 密钥（必填） | — |
| `BAILIAN_API_ENDPOINT` | 百炼 API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MILVUS_HOST` | Milvus 服务地址 | `localhost` |
| `MILVUS_PORT` | Milvus 服务端口 | `19530` |
| `MILVUS_DB` | Milvus 数据库名 | `Four_classic` |
| `DB_HOST` | MySQL 地址 | `localhost` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | MySQL 用户名 | `root` |
| `DB_PASSWORD` | MySQL 密码 | — |
| `DB_NAME` | MySQL 数据库名 | `fastapi_study` |
| `JWT_SECRET_KEY` | JWT 签名密钥（必填） | — |
| `CHUNK_SIZE` | 文本切片大小（字符数） | `500` |
| `CHUNK_OVERLAP` | 切片重叠字符数 | `100` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

---

## 常见问题

### Q: 启动后端报错 `ModuleNotFoundError`

确保在项目根目录运行 `python main.py`，且已安装所有依赖：

```bash
pip install -r requirements.txt
```

### Q: 问答返回 "目前尚未了解这个方面的知识"

可能原因：
1. Milvus 未启动或连接失败 — 检查 `MILVUS_HOST` 和 `MILVUS_PORT`
2. 数据未入库 — 运行 `fgcnrag/fgcn/insert_data.py` 导入数据
3. 问题超出四大名著范围

### Q: 前端请求报 401

- 确认已先注册并登录获取 Token
- Token 过期需重新登录（默认有效期 24 小时）
- 检查浏览器 `localStorage` 中是否存在 `auth_token`

### Q: Milvus 如何安装

推荐使用 Docker：

```bash
docker run -d --name milvus-standalone \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:latest
```

### Q: bcrypt 警告 `error reading bcrypt version`

passlib 与新版本 bcrypt 的兼容性提示，不影响密码哈希和验证功能。

---

## License

MIT License
