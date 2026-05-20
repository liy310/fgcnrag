# 林黛玉智能对话系统

一个基于 FastAPI + React 构建的智能对话应用，集成林黛玉角色 Agent 和四大名著知识问答系统。

## 项目概述

本项目是一个**前后端分离**的全栈应用，包含两个核心模块：

1. **林黛玉Agent** — 以《红楼梦》中林黛玉为原型的智能对话系统，支持对话（含情绪共情）、飞花令、对对联、诗词鉴赏、作文点评、情绪疏导等功能
2. **四大名著问答** — 基于 RAG 技术的四大名著知识问答系统（fgcnrag 模块）

---

## 目录结构

```
lindaiyu/
├── main.py                           # FastAPI 后端主入口
├── requirements.txt                  # Python 依赖
├── .env                              # 环境变量配置
│
├── frontend/                         # React 前端项目
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx                  # 入口文件
│       ├── App.tsx                   # 主应用组件（含路由和认证）
│       ├── api.ts                    # API 调用封装
│       └── pages/
│           ├── Login.tsx             # 登录/注册页面
│           ├── SelectMode.tsx        # 功能选择页
│           ├── LDYHome.tsx           # 林黛玉首页
│           ├── Chat.tsx              # 对话页面
│           ├── FlyFlower.tsx         # 飞花令游戏
│           ├── PoetryAppreciate.tsx  # 诗词鉴赏
│           ├── Couplet.tsx           # 对对联
│           └── EssayReview.tsx       # 作文点评
│
├── ldyagent/                         # 林黛玉 Agent 核心模块
│   ├── api/                          # 接口层（纯路由，无业务逻辑）
│   │   ├── auth.py                   # 用户认证接口（注册/登录/获取用户）
│   │   ├── chat_emotion.py           # 对话 + 情绪分析接口
│   │   ├── poetry.py                 # 诗词相关接口（飞花令/对联/鉴赏）
│   │   └── academic.py               # 学业相关接口（作文点评）
│   │
│   ├── chain/                        # 业务编排层（LLM 调用 + 逻辑编排）
│   │   └── ldy_rag.py                # LinDaiyuChain：对话、情绪疏导、作文点评
│   │
│   ├── services/                     # 服务层（纯业务逻辑，可独立测试）
│   │   ├── flying_flower_service.py  # 飞花令：校验/去重/会话管理/AI对诗
│   │   ├── couplet_service.py        # 对联：格律校验/平仄检查/意境匹配
│   │   ├── emotion_analyzer.py       # 情绪分析：12种情绪识别/共情生成
│   │   ├── memory_compressor.py      # 记忆压缩：对话历史摘要（3-2-2000策略）
│   │   └── document_loader.py        # 文档加载（支持 TXT/PDF/DOCX）
│   │
│   ├── database/                     # 数据库层（CRUD 操作）
│   │   ├── mysql_init.py             # MySQL 初始化 + 4张表的完整 CRUD
│   │   └── user_db.py                # 用户数据库（users 表）
│   │
│   ├── persona/
│   │   └── lin_persona.py            # 林黛玉角色设定（系统提示词/问候语）
│   │
│   ├── auth.py                       # JWT 认证工具函数
│   ├── config.py                     # 全局配置（环境变量加载）
│   └── init_database.py              # 数据库初始化脚本
│
└── fgcnrag/                          # 四大名著问答模块
    ├── fgcn/
    │   ├── api/chat.py               # 问答接口
    │   ├── chain/qa_rag.py           # RAG 问答链
    │   └── retriever/                # 向量检索器
    └── data/                         # 四大名著原文数据
```

---

## 三层架构设计

系统采用清晰的**三层架构**，职责分明：

```
┌─────────────────────────────────────────────────────────┐
│                    接口层 (api/)                         │
│  纯路由定义、请求/响应模型、参数校验                     │
│  唯一职责：接收 HTTP 请求，调用服务层，返回响应           │
│  示例：poetry.py 中 /flyflower/start → ff_start_game()   │
├─────────────────────────────────────────────────────────┤
│                 业务编排层 (chain/)                       │
│  LLM 调用编排、Prompt 构建、会话状态管理                  │
│  位于 api 和 services 之间，协调多个服务完成复杂业务       │
│  示例：ldy_rag.py 中 _build_messages() 组合各模块         │
├─────────────────────────────────────────────────────────┤
│                  服务层 (services/)                       │
│  纯业务逻辑函数，不依赖 FastAPI，可独立单元测试            │
│  通过参数接收 llm_caller 回调，与 LLM 解耦                │
│  示例：flying_flower_service.py 的 validate_poem()        │
├─────────────────────────────────────────────────────────┤
│                  数据库层 (database/)                    │
│  纯 CRUD 操作，不包含业务逻辑                            │
│  示例：mysql_init.py 的 get_conversations()               │
└─────────────────────────────────────────────────────────┘
```

**设计原则**：
- 每层只依赖下一层，不反向依赖
- 服务层通过 `llm_caller` 回调注入调用 LLM 的能力，而非直接引用 `chain`
- API 层不包含任何业务逻辑，仅做请求转发
- 服务层函数为纯函数设计，可独立测试

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- DeepSeek API Key（用于 LLM 调用）
- MySQL 8.0+（可选，对话记录和情绪数据持久化）

### 1. 配置环境变量

创建 `.env` 文件（放在项目根目录）：

```env
# DeepSeek API 配置（必填）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com

# MySQL 配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=lindaiyu

# JWT 密钥（可选，有默认值）
SECRET_KEY=your_secret_key
```

### 2. 启动后端

```bash
pip install -r requirements.txt
python main.py
```

服务运行在 `http://127.0.0.1:8080`，API 文档见 `http://127.0.0.1:8080/docs`。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 功能模块

### 一、林黛玉 Agent

| 功能 | 接口 | 说明 | 认证 |
|------|------|------|------|
| 用户登录 | `POST /api/v1/auth/login/access-token` | 登录获取 JWT | 否 |
| 用户注册 | `POST /api/v1/auth/register` | 注册新账户 | 否 |
| 获取用户信息 | `GET /api/v1/auth/me` | 当前登录用户信息 | 是 |
| 对话聊天 | `POST /ldy/chat` | 带情绪分析的智能对话（含记忆压缩） | 是 |
| 情绪疏导 | `POST /ldy/emotion_support` | 专业情绪疏导（共情 + 建议） | 是 |
| 诗词鉴赏 | `POST /ldy/poetry/appreciate` | 分析诗词意境与情感 | 是 |
| 飞花令开始 | `POST /ldy/poetry/flyflower/start` | 发牌局，黛玉先对第 1 字 | 是 |
| 飞花令对诗 | `POST /ldy/poetry/flyflower` | 用户提交诗句，服务层校验 + AI 对诗 | 是 |
| 飞花令统计 | `POST /ldy/poetry/flyflower/stats` | 用户飞花令战绩统计 | 是 |
| 对对联 | `POST /ldy/poetry/couplet` | 基于平仄格律的对联匹配 | 否 |
| 作文点评 | `POST /ldy/academic/essay_review` | 黛玉风格的学生作文点评 | 否 |

### 二、四大名著问答

| 功能 | 接口 | 说明 | 认证 |
|------|------|------|------|
| 知识问答 | `POST /fgcn/chat` | 基于 RAG 的四大名著问答 | 否 |

---

## 核心特性实现方案

### 1. 林黛玉对话系统（chat）

**位置**：`chain/ldy_rag.py` → `LinDaiyuChain.chat()`

**处理流程**：
```
用户输入
    ↓
情绪分析 (emotion_analyzer.py) → 检测情绪 + 生成共情语
    ↓
构建 Prompt (ldy_rag.py)：
    ┌──────────────────────────────────────────┐
    │  1. System Prompt（林黛玉人设）            │
    │  2. 情绪响应指令 + 对应诗词引用             │
    │  3. 预生成共情回复（要求LLM先共情再回答）    │
    │  4. 对话历史（含记忆压缩后的摘要）           │
    │  5. 用户输入                              │
    └──────────────────────────────────────────┘
    ↓
调用 DeepSeek V4 Flash LLM
    ↓
保存对话 + 情绪数据到 MySQL
    ↓
返回 {answer, session_id, emotion_detected}
```

**关键设计**：
- 先在 `emotion_analyzer` 中分析情绪并生成共情语，再注入 Prompt 要求 LLM 先共情后作答，确保情感支持效果
- System Prompt 包含详细的情绪识别与共情要求指令

### 2. 对话记忆压缩（memory compression）

**位置**：`services/memory_compressor.py` + `chain/ldy_rag.py::_get_conversation_context()`

**3-2-2000 策略**：
```
对话历史(最多取20条)
    ↓ 反转成正序
[历史... | 最近6条(3轮)]
    ↓ 总字符 > 2000?          ──否──→ 直接拼接返回
    ↓ 是
调用 LLM 进行增量压缩
    ↓
已有摘要 + 本次历史 → 新摘要(≤150字)
    ↓
存入 session 表 memory_summary 字段
    ↓
返回 "【长期记忆】摘要 + 【最近对话】完整保留"
```

**设计理由**：
- **保留 3 轮完整**：一般用户倾诉需要 2-3 轮才能完整表达，保留足够上下文让 LLM 理解当前话题
- **2000 字阈值**：中文字均约 3 个 token，2000 字 ≈ 6000 tokens，远低于主流 LLM 上下文窗口，但当压缩发生时说明用户已进行较长的深层交流
- **增量摘要**：每次在已有摘要基础上追加新增对话，避免重新压缩全部历史浪费 tokens
- **摘要 ≤ 150 字**：足够保留关键信息（用户身份、核心话题、情绪变化、重要建议）且不会挤占上下文窗口

### 3. 飞花令游戏（flying flower）

**位置**：`services/flying_flower_service.py`（约 700 行）

**游戏规则**：
- 7 个位置轮流嵌入关键字，AI 和用户交替对诗
- 用户有 3 次机会，格式错误或重复均消耗次数
- 同一局中所有诗句不可重复（双方均受约束）
- AI 重复诗句时自动判 AI 认输

**核心函数**：

| 函数 | 职责 |
|------|------|
| `validate_poem(poem, keyword, position)` | 校验七言诗：7 字、全中文、关键字在指定位置（支持多字关键字切片） |
| `start_game(keyword, difficulty, user_id, llm_caller)` | 创建会话、AI 出第一句 |
| `process_turn(keyword, user_line, user_position, ...)` | 完整游戏循环：格式校验 → 去重校验 → AI 对诗 → AI 去重硬校验 → 状态更新 |

**诗句去重机制**：
```python
_session.used_poems = []  # 本局所有诗句

# 用户提交时校验
if poem in used_poems:
    fail_count += 1  # 消耗一次机会

# AI 回复后硬校验
ai_poem = ai_line[:7]
if ai_poem in used_poems:
    # AI 重复 → AI 认输 → 用户获胜
    save_record(is_success=True)
    destroy_session()
    return victory_message
```

**会话管理**：
- 使用内存 dict `_game_sessions` 存储活跃游戏会话
- 通过 `_user_active_sessions[user_id] → session_id` 映射兼容前端未传 session_id 的情况
- 游戏结束时 `_destroy_session()` 彻底清理



### 4. 对对联（couplet）

**位置**：`services/couplet_service.py`

**处理流程**：
```
用户输入对联
    ↓
validate_couplet() → 字数(3-20)/字符(仅中文+标点)校验
    ↓
build_couplet_prompt() → 构建含平仄规则的 LLM Prompt
    ↓
调用 DeepSeek → 生成下联/上联
    ↓
parse_couplet_response() → 从 LLM 回复提取对联
    ↓
validate_final_couplet() → 最终校验
    ↓
generate_couplet_response() → 生成含感慨语的回复
```

**平仄校验规则**：
- 七言定式：上联「仄仄平平平仄仄」/ 下联「平平仄仄仄平平」
- 五言定式：上联「平平平仄仄」/ 下联「仄仄仄平平」
- 末字四声映射：平(一声/二声) → 平；上(三声)/去(四声)/入 → 仄
- 校验支持降级为宽松模式（仅校验字数）

**关键设计**：
- 50+ 条多样化话术（成功感慨 8 条、格式提醒 4 条、致歉 6 条），避免机械回复
- 硬检查 AI 是否直接复制用户输入（敷衍检测）
- `generate_couplet_response()` 支持感慨语中动态嵌入用户对联关键词

### 5. 情绪分析（emotion analysis）

**位置**：`services/emotion_analyzer.py` + `persona/lin_persona.py`（情绪关键词配置解耦到配置层）

| 方法 | 职责 |
|------|------|
| `analyze(text)` | 基于关键词规则识别 12 种情绪，返回 (emotion, intensity, keywords) |
| `generate_empathy_response(emotion, text)` | 预生成共情语，在 LLM 回复前先输出共情 |
| `get_poetry_for_emotion(emotion)` | 根据情绪返回对应诗词引用 |

**共情策略**：先检测情绪并生成共情语 → 注入 Prompt 要求 LLM 先共情再回答 → 确保每轮对话都有情感支持。

**12种情绪类型**：

| 情绪 | 关键词示例 | 学生场景 | 对应诗词 |
|------|-----------|---------|---------|
| 焦虑 | 考试、升学、成绩、学业压力、紧张 | 考前焦虑、升学压力 | 《葬花吟》 |
| 自卑 | 不如别人、长相、家境、自我否定 | 成绩不如同学、外貌焦虑 | 《咏白海棠》 |
| 烦躁易怒 | 发脾气、静不下心、烦死了、火大 | 一点小事就炸、学不进去 | 《秋窗风雨夕》 |
| 抑郁低落 | 莫名难过、提不起劲、消沉、悲观 | 长期情绪低落、厌世 | 《葬花吟》 |
| 孤独孤单 | 没人理解、不合群、融不进去 | 宿舍/班级融不进、没朋友 | 《问菊》 |
| 嫉妒 | 羡慕、眼红、攀比、不平衡 | 羡慕别人成绩/家境/人缘 | 《桃花行》 |
| 叛逆抵触 | 反感、对着干、别管我、不服气 | 抗拒家长老师管教 | 《红楼梦》判词 |
| 迷茫无助 | 没目标、不知所措、不知道意义 | 不知道学习意义、没方向 | 《红楼梦》判词 |
| 愧疚自责 | 对不起、辜负、内疚、后悔 | 考差自责、辜负家人期待 | 《红豆词》 |
| 恐惧胆怯 | 害怕、怕发言、怕社交、胆小 | 怕被批评、怕当众说话、社恐 | 《五美吟》 |
| 厌学倦怠 | 不想上学、学不进去、身心疲惫 | 逃避学习、写不动作业 | 《唐多令》 |
| 委屈憋屈 | 被误会、被冤枉、有苦说不出 | 被老师/家长误解 | 《秋窗风雨夕》 |

**解耦设计**：情绪关键词和诗词引用配置在 `persona/lin_persona.py` 的 `EMOTION_KEYWORDS` 字典中，`emotion_analyzer.py` 仅通过 `from ldyagent.persona.lin_persona import EMOTION_KEYWORDS` 引入。新增/修改情绪只需改配置层，服务层无需改动。

### 6. 作文点评（essay review）

**位置**：`chain/ldy_rag.py::LinDaiyuChain.essay_review()`

**点评风格**：半文半白、先夸后弹、诗词典故、傲娇收尾
- 以"小友"称呼对方
- 先含蓄夸赞可取之处
- 再娇嗔吐槽俗套/生硬/堆砌问题
- 最后一句诗意傲娇收尾

### 7. 认证系统

**位置**：`ldyagent/auth.py` + `ldyagent/api/auth.py`

- JWT 无状态认证（HS256）
- Token 含用户 ID + 过期时间（默认 30 天）
- `get_current_user` 作为 FastAPI Depends 保护需要认证的接口
- 密码 bcrypt 哈希存储

---

## 数据模型（MySQL）

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | 主键 |
| username | VARCHAR(255) UNIQUE | 用户名 |
| email | VARCHAR(255) UNIQUE | 邮箱 |
| hashed_password | VARCHAR(255) | 哈希后的密码 |
| is_active | TINYINT | 是否激活 |
| is_superuser | TINYINT | 是否超级用户 |
| created_at | TIMESTAMP | 创建时间 |

### ldy_sessions（会话表）

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | VARCHAR(64) PK | UUID 会话标识 |
| user_id | VARCHAR(64) | 用户标识 |
| user_nickname | VARCHAR(100) | 用户昵称 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后交互时间 |
| emotion_state | VARCHAR(20) | 当前情绪状态 |
| interaction_count | INT | 交互次数 |
| memory_summary | TEXT | 压缩记忆摘要 |

### ldy_conversations（对话历史表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO_INCREMENT | 自增主键 |
| session_id | VARCHAR(64) FK | 关联会话 |
| role | ENUM('user','assistant') | 角色 |
| content | TEXT | 对话内容 |
| emotion_tag | VARCHAR(50) | 情绪标签 |
| created_at | DATETIME | 时间戳 |

### ldy_emotions（情绪记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO_INCREMENT | 自增主键 |
| session_id | VARCHAR(64) FK | 关联会话 |
| user_emotion | VARCHAR(50) | 用户情绪 |
| emotion_intensity | FLOAT | 情绪强度 0-1 |
| ldy_response | TEXT | Agent 回复 |
| emotion_keywords | JSON | 情绪关键词 |
| created_at | DATETIME | 时间戳 |

### ldy_flying_flower_records（飞花令记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO_INCREMENT | 自增主键 |
| user_id | VARCHAR(64) | 用户 ID |
| keyword | VARCHAR(20) | 关键字 |
| difficulty | VARCHAR(20) | 难度 |
| total_rounds | INT | 完成轮数 |
| is_surrender | TINYINT | 是否认输 |
| is_success | TINYINT | 是否胜出 |
| created_at | DATETIME | 游戏时间 |

---

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **LLM**: DeepSeek V4 Flash（via REST API）
- **数据库**: MySQL 8.0
- **认证**: JWT（PyJWT + bcrypt）
- **日志**: Loguru

### 前端
- **框架**: React 18
- **路由**: React Router DOM 6（HashRouter）
- **构建工具**: Vite
- **语言**: TypeScript
- **样式**: CSS

---

## API 使用手册

### 认证相关

所有需要认证的接口需在请求头中携带 Token：

```
Authorization: Bearer <your_token>
```

#### 1. 用户注册 `POST /api/v1/auth/register`

```json
// Request
{ "username": "xiaoming", "email": "xiaoming@example.com", "password": "123456" }
// Response
{ "id": 1, "username": "xiaoming", "email": "xiaoming@example.com", "is_active": true }
```

#### 2. 用户登录 `POST /api/v1/auth/login/access-token`

```
Content-Type: application/x-www-form-urlencoded
username=xiaoming&password=123456

// Response: { "access_token": "eyJ...", "token_type": "bearer" }
```

#### 3. 获取当前用户 `GET /api/v1/auth/me`

```
Authorization: Bearer <your_token>

// Response: { "id": 1, "username": "xiaoming", "email": "xiaoming@example.com", "is_active": true }
```

### 对话与情绪

#### 4. 对话聊天 `POST /ldy/chat`

```json
// Request (Authorization: Bearer <token>)
{ "query": "我最近感到很迷茫，不知道该怎么办", "user_nickname": "小友" }

// Response
{
    "answer": "小友，颦儿听闻此言，深知你心中烦闷...",
    "session_id": "xxx",
    "emotion_detected": "迷茫",
    "emotion_intensity": 0.85,
    "empathy": "颦儿懂得这份迷茫..."
}
```

### 诗词相关

#### 5. 诗词鉴赏 `POST /ldy/poetry/appreciate`

```json
// Request
{ "poetry_text": "花谢花飞花满天，红消香断有谁怜" }
// Response
{ "result": "鉴赏：...\n\n情感：..." }
```

#### 6. 飞花令开始 `POST /ldy/poetry/flyflower/start`

```json
// Request (Authorization: Bearer <token>)
{ "keyword": "花", "difficulty": "normal" }

// Response
{
    "ai_line": "花近高楼伤客心，万方对此难为情",
    "ai_position": 1,
    "user_position": 2,
    "current_round": 1,
    "is_game_over": false,
    "message": "小友，该你了。",
    "session_id": "uuid-xxx"
}
```

#### 7. 飞花令继续 `POST /ldy/poetry/flyflower`

```json
// Request (Authorization: Bearer <token>)
{
    "keyword": "花",
    "user_line": "花间一壶酒",
    "user_position": 2,
    "current_round": 1,
    "difficulty": "normal",
    "session_id": "uuid-xxx"
}

// Response
{
    "ai_line": "感时花溅泪，恨别鸟惊心",
    "ai_position": 3,
    "user_position": 4,
    "is_game_over": false,
    "message": "不错，轮到你了。",
    "total_rounds": 1,
    "session_id": "uuid-xxx"
}
```

#### 8. 飞花令统计 `POST /ldy/poetry/flyflower/stats`

```json
// Response (Authorization: Bearer <token>)
{ "best_rounds": 5, "total_games": 10, "success_games": 3 }
```

#### 9. 对对联 `POST /ldy/poetry/couplet`

```json
// Request
{ "couplet": "寒塘渡鹤影", "couplet_type": "下联" }

// Response
{ "success": true, "matched_line": "冷月葬花魂", "emotion": "此联意境清雅...", "message": "...", "is_reminded": false }
```

#### 10. 作文点评 `POST /ldy/academic/essay_review`

```json
// Request
{ "essay_content": "我的妈妈..." }

// Response
{ "review": "小友此文，倒有几分真情...（黛玉风格点评）" }
```

### 四大名著问答

#### 11. 知识问答 `POST /fgcn/chat`

```json
// Request
{ "query": "贾宝玉和林黛玉是什么关系？" }
// Response
{ "answer": "贾宝玉和林黛玉是姑表兄妹..." }
```

---

## 林黛玉角色设定

- **身份**: 金陵十二钗正册之首，绛珠仙草转世
- **性格**: 才情横溢、多愁善感、清高孤傲、略带娇嗔
- **语言风格**: 半文半白，善用典故诗词，温柔吐槽
- **自称**: "颦儿"
- **称呼对方**: "小友"、"这位同学"

---

## 常见问题

### Q: 飞花令刷新页面后"会话已过期"？
A: 新版已修复。服务层维护 `user_id → session_id` 映射，前端未传 session_id 时会自动按用户 ID 回退匹配活跃会话。

### Q: 飞花令难度关键字有哪些？
A: 三档难度：
- **easy**: 花、月、风、春、山、水、云、雨、天、江、夜、人、酒、雪（常用字）
- **normal**: 柳、荷、梅、兰、舟、楼、烟、霞、琴、书、君、客、梦、情、秋（稍难）
- **hard**: 笛、雁、帆、尘、路、乡、寒、暖、霜、露

### Q: 如何添加新的情绪类型？
A: 在 `services/emotion_analyzer.py` 的情绪识别关键词字典中添加对应关键词即可。

### Q: 对话记忆会丢失吗？
A: 短期不会。最近 3 轮完整保留，超过 2000 字符后早期历史被压缩为摘要存储在 MySQL `ldy_sessions.memory_summary` 字段中。

### Q: 忘记密码怎么办？
A: 当前版本未提供找回密码功能，请使用新账户注册。

### Q: 如何设置超级用户？
A: 有以下几种方式：

**1. 命令行设置（需要进入 MySQL）**
```sql
UPDATE users SET is_superuser = 1 WHERE username = '你的用户名';
```

**2. 通过 Python 代码**
```python
from ldyagent.database.user_db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(
    "UPDATE users SET is_superuser = 1 WHERE username = %s",
    ("用户名",)
)
conn.commit()
conn.close()
```

**3. 创建超级用户**
```python
from ldyagent.database.user_db import get_db_connection
from hash统一password import hash_password

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO users (username, email, hashed_password, is_superuser) VALUES (%s, %s, %s, 1)",
    ("admin", "admin@example.com", hash_password("密码"))
)
conn.commit()
conn.close()
```

---

## License

MIT License
