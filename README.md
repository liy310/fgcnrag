# 林黛玉智能对话系统

一个基于 FastAPI + React 构建的智能对话应用，集成林黛玉角色 Agent 和四大名著知识问答系统。

## 项目概述

本项目是一个**前后端分离**的全栈应用，包含两个核心模块：

1. **林黛玉Agent** - 以《红楼梦》中林黛玉为原型的智能对话系统，支持诗词、对联、情绪疏导等功能
2. **四大名著问答** - 基于 RAG 技术的四大名著知识问答系统

---

## 目录结构

```
lindaiyu/
├── main.py                      # FastAPI 后端主入口
├── requirements.txt             # Python 依赖
│
├── frontend/                     # React 前端项目
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx             # 入口文件
│       ├── App.tsx              # 主应用组件（含路由和认证）
│       ├── api.ts               # API 调用封装
│       ├── index.css            # 全局样式
│       └── pages/
│           ├── Login.tsx        # 登录/注册页面
│           ├── SelectMode.tsx   # 功能选择页
│           ├── FourClassicQA.tsx # 四大名著问答
│           ├── LDYHome.tsx      # 林黛玉首页
│           ├── Chat.tsx         # 对话页面
│           ├── FlyFlower.tsx    # 飞花令游戏
│           ├── PoetryAppreciate.tsx # 诗词鉴赏
│           ├── Couplet.tsx      # 对对联
│           └── EssayReview.tsx  # 作文点评
│
├── ldyagent/                    # 林黛玉Agent模块
│   ├── api/
│   │   ├── auth.py             # 用户认证接口
│   │   ├── chat_emotion.py     # 对话+情绪分析
│   │   ├── poetry.py           # 诗词相关接口
│   │   └── academic.py         # 学业相关接口
│   ├── auth.py                  # JWT认证工具
│   ├── chain/
│   │   └── ldy_rag.py          # 林黛玉RAG实现
│   ├── services/
│   │   ├── poetry_service.py
│   │   └── emotion_analyzer.py # 情绪分析
│   ├── persona/
│   │   └── lin_persona.py      # 林黛玉人设
│   └── database/
│       └── user_db.py          # 用户数据库
│
└── fgcnrag/                     # 四大名著问答模块
    ├── fgcn/
    │   ├── api/chat.py          # 问答接口
    │   ├── chain/qa_rag.py      # RAG链
    │   └── retriever/          # 检索器
    └── data/                    # 四大名著原文数据
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 通义千问 API Key（用于 LLM 调用）

### 1. 启动后端

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 2. 启动前端

```bash
cd frontend

# 安装 Node 依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# 必填：通义千问 API Key
DASHSCOPE_API_KEY=your_api_key_here
```

---

## 功能模块

### 一、林黛玉Agent

| 功能 | 接口 | 说明 | 认证 |
|------|------|------|------|
| 用户登录 | `POST /api/v1/auth/login/access-token` | 登录获取JWT | 否 |
| 用户注册 | `POST /api/v1/auth/register` | 注册新账户 | 否 |
| 获取用户信息 | `GET /api/v1/auth/me` | 当前登录用户 | 是 |
| 对话聊天 | `POST /ldy/chat` | 带情绪分析的智能对话 | 是 |
| 诗词鉴赏 | `POST /ldy/poetry/appreciate` | 分析诗词并鉴赏 | 是 |
| 飞花令 | `POST /ldy/poetry/flyflower` | 飞花令游戏 | 是 |
| 对对联 | `POST /ldy/poetry/couplet` | 对联匹配 | 是 |
| 作文点评 | `POST /ldy/academic/essay_review` | 点评学生作文 | 是 |

### 二、四大名著问答

| 功能 | 接口 | 说明 | 认证 |
|------|------|------|------|
| 知识问答 | `POST /fgcn/chat` | 基于四大名著内容的问答 | 否 |

---

## 代码方案解释

### 后端架构

#### 1. FastAPI 主入口 (`main.py`)

```
main.py
    ├── FastAPI 应用配置
    ├── CORS 中间件配置
    └── 路由注册
            ├── /api/v1/auth/*    (认证)
            ├── /fgcn/*          (四大名著)
            └── /ldy/*           (林黛玉Agent)
```

**关键设计**：
- 使用 `include_router` 模块化注册路由
- CORS 配置允许前端跨域访问
- 路由前缀统一管理，便于维护

#### 2. 认证系统

```
ldyagent/auth.py
    ├── create_access_token()    # JWT token 生成
    ├── verify_token()           # Token 验证
    └── get_current_user()        # 依赖注入获取当前用户
```

**安全机制**：
- JWT (JSON Web Token) 无状态认证
- Token 包含用户 ID 和过期时间
- 依赖注入保护需要认证的接口

#### 3. 用户认证 API (`ldyagent/api/auth.py`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login/access-token` | POST | 用户登录 |
| `/api/v1/auth/me` | GET | 获取当前用户信息 |

**数据流**：
```
注册 → 密码哈希 → 存储到 MySQL → 返回用户信息
登录 → 验证密码 → 生成 JWT → 返回 token
```

#### 4. 林黛玉对话系统 (`ldyagent/api/chat_emotion.py`)

```
用户输入
    ↓
情绪分析 (emotion_analyzer.py)
    ↓
RAG 检索 (ldy_rag.py) + LLM 生成
    ↓
林黛玉人设注入 (lin_persona.py)
    ↓
返回回复 + 情绪标签 + 同理心回复
```

**情绪支持**：焦虑、委屈、迷茫、失落、愤怒、开心、孤独

#### 5. 诗词相关功能 (`ldyagent/api/poetry.py`)

| 功能 | 说明 |
|------|------|
| 诗词鉴赏 | 分析诗词意境、情感、艺术手法 |
| 飞花令 | 回合制古诗词接龙游戏 |
| 对对联 | 匹配经典下联 |

---

### 前端架构

#### 1. React 路由设计 (`App.tsx`)

```
App
├── AuthProvider (全局状态)
│       ├── user: 用户信息
│       ├── token: JWT token
│       ├── isLoading: 加载状态
│       └── login/register/logout
│
├── HashRouter
│       ├── /login           (公开)
│       ├── /select           (Protected)
│       ├── /four-classic     (Protected)
│       └── /ldy/*            (Protected)
│
└── ProtectedRoute (路由守卫)
```

#### 2. 认证状态管理

```
AuthProvider
├── 初始化
│   └── 从 localStorage 读取 token
│       → 调用 /auth/me 验证
│       → 设置 user 和 isLoading
│
├── login
│   └── 调用 /auth/login
│       → 保存 token 到 localStorage
│       → 设置 user
│
└── logout
    └── 清除 token 和 user
```

#### 3. 路由守卫机制

```tsx
function ProtectedRoute({ children }) {
  const { token, isLoading } = useAuth();
  
  // 加载中：保持当前页面，等待认证状态确定
  if (isLoading) return null;
  
  // 已认证：显示内容
  if (token) return <>{children}</>;
  
  // 未认证：重定向到登录
  return <Navigate to="/login" />;
}
```

**关键点**：使用 `isLoading` 状态避免页面刷新时闪烁或错误重定向。

#### 4. API 调用封装 (`api.ts`)

```typescript
// Token 管理
tokenManager
├── getToken()      // 获取存储的 token
├── setToken()       // 保存 token
└── removeToken()    // 删除 token

// API 调用
authApi
├── login()          // POST /auth/login/access-token
├── register()       // POST /auth/register
└── getMe()          // GET /auth/me
```

---

## API 使用手册

### 认证相关

所有需要认证的接口需要在请求头中携带 Token：

```
Authorization: Bearer <your_token>
```

#### 1. 用户注册 `POST /api/v1/auth/register`

**请求：**
```json
{
    "username": "xiaoming",
    "email": "xiaoming@example.com",
    "password": "123456"
}
```

**响应：**
```json
{
    "id": 1,
    "username": "xiaoming",
    "email": "xiaoming@example.com",
    "is_active": true
}
```

#### 2. 用户登录 `POST /api/v1/auth/login/access-token`

**请求：**
```
Content-Type: application/x-www-form-urlencoded

username=xiaoming&password=123456
```

**响应：**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

#### 3. 获取当前用户 `GET /api/v1/auth/me`

**请求头：**
```
Authorization: Bearer <your_token>
```

**响应：**
```json
{
    "id": 1,
    "username": "xiaoming",
    "email": "xiaoming@example.com",
    "is_active": true
}
```

### 功能接口

#### 4. 对话聊天 `POST /ldy/chat`

**请求头：**
```
Authorization: Bearer <your_token>
```

**请求体：**
```json
{
    "query": "我最近感到很迷茫，不知道该怎么办",
    "user_nickname": "小友"
}
```

**响应：**
```json
{
    "answer": "小友，颦儿听闻此言，深知你心中烦闷...",
    "session_id": "1",
    "emotion_detected": "迷茫",
    "emotion_intensity": 0.85,
    "empathy": "颦儿懂得这份迷茫..."
}
```

#### 5. 诗词鉴赏 `POST /ldy/poetry/appreciate`

**请求头：**
```
Authorization: Bearer <your_token>
```

**请求体：**
```json
{
    "poetry_text": "花谢花飞花满天，红消香断有谁怜"
}
```

**响应：**
```json
{
    "result": "鉴赏：...\n\n情感：..."
}
```

#### 6. 飞花令开始 `POST /ldy/poetry/flyflower/start`

**请求头：**
```
Authorization: Bearer <your_token>
```

**请求体：**
```json
{
    "keyword": "花",
    "difficulty": "normal"
}
```

**响应：**
```json
{
    "ai_line": "花近高楼伤客心，万方对此难为情",
    "next_position": 2,
    "next_round": 1,
    "is_game_over": false,
    "message": "小友，该你了。"
}
```

#### 7. 飞花令继续 `POST /ldy/poetry/flyflower`

**请求体：**
```json
{
    "keyword": "花",
    "user_line": "花间一壶酒，独酌无相亲",
    "current_position": 2,
    "current_round": 1,
    "difficulty": "normal"
}
```

#### 8. 对对联 `POST /ldy/poetry/couplet`

**请求体：**
```json
{
    "couplet": "寒塘渡鹤影",
    "couplet_type": "下联"
}
```

**响应：**
```json
{
    "matched_line": "冷月葬花魂"
}
```

#### 9. 四大名著问答 `POST /fgcn/chat`

**请求体：**
```json
{
    "query": "贾宝玉和林黛玉是什么关系？"
}
```

**响应：**
```json
{
    "answer": "贾宝玉和林黛玉是..."
}
```

---

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **LLM**: 通义千问 (DeepSeek V4 Flash)
- **向量模型**: text-embedding-v4
- **用户数据库**: MySQL（可选，需配置）
- **RAG**: LangChain

### 前端
- **框架**: React 18
- **路由**: React Router DOM 6
- **构建工具**: Vite
- **语言**: TypeScript
- **样式**: CSS

---

## 林黛玉角色设定

本系统的林黛玉 Agent 以《红楼梦》中的林黛玉为原型：

- **身份**: 金陵十二钗正册之首，绛珠仙草转世
- **性格**: 才情横溢、多愁善感、清高孤傲
- **语言风格**: 半文半白，善用典故诗词
- **称呼**: 自称"颦儿"，称对方为"小友"、"这位同学"

### 支持的情绪疏导

| 情绪 | 说明 |
|------|------|
| 焦虑 | 考试压力、工作压力等 |
| 委屈 | 被人误解、受到不公待遇 |
| 迷茫 | 人生方向、职业选择困惑 |
| 失落 | 失去重要的人或事 |
| 愤怒 | 对某事感到不满 |
| 开心 | 分享喜悦时刻 |
| 孤独 | 渴望陪伴和理解 |

---

## 常见问题

### Q: 飞花令每次刷新页面会话丢失？
A: 现在使用用户ID作为session_id，登录后所有会话记忆都会保持。

### Q: 如何自定义难度关键字？
A: 修改 `ldyagent/api/poetry.py` 中的 `DIFFICULTY_KEYWORDS` 字典。

### Q: 如何添加新的情绪类型？
A: 修改 `ldyagent/services/emotion_analyzer.py` 中的情绪识别逻辑。

### Q: 忘记密码怎么办？
A: 当前版本未提供找回密码功能，请使用新账户注册。

---

## License

MIT License
