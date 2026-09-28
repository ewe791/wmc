# 电商智能客服 AI 服务

一个面向电商平台的**智能客服 AI 服务**。作为独立的后端服务，被上游业务主服务（customer-service）通过内部接口调用，承接其转发的用户咨询。

核心定位是**只读的智能决策**：基于 LangChain 编排 LLM Agent，自主调用商品、库存、订单、物流、售后等只读业务工具完成数据取证，并以结构化输出返回「回答 / 反问 / 拒答 / 转人工」四类决策。

> **设计上的一个关键选择**：本服务从不真正执行取消订单、退款、改地址等写操作。
> 大模型存在不确定性，只读能保证最坏情况也只是「答错」，用户可以自行核实，而不会造成资金或资产损失。

---

## 服务边界

```
用户在电商前端提问
        │
        ▼
┌──────────────────────┐
│  customer-service    │   业务主服务：会话管理、消息落库、工单、前端推送
└──────────┬───────────┘
           │  HTTP 内部接口调用
           │  X-Internal-Service-Token + Authorization: Bearer <用户 JWT>
           ▼
┌──────────────────────┐
│  ai-service          │   ★ 本项目：只负责「想清楚该怎么答」
└──────────┬───────────┘
           │  HTTP 只读调用（携带用户令牌）
           ▼
┌──────────────────────┐
│  ecommerce-service   │   业务数据服务：商品、订单、物流、售后
└──────────────────────┘
```

两个服务之间通过**统一事件结构**协作：

```json
{
  "event_type": "run_completed",
  "event_data": { "run_id": "run_xxx", "...": "..." }
}
```

上游只需按 `event_type` 分发，不关心 AI 服务的内部实现。

---

## 技术栈

| 类别 | 组件 |
|---|---|
| 语言 | Python >= 3.12 |
| Web 框架 | FastAPI >= 0.116 |
| ASGI 服务器 | Uvicorn[standard] >= 0.35 |
| ORM | SQLAlchemy >= 2.0（async） |
| 数据库 | PostgreSQL + psycopg 3 |
| Agent 编排 | LangChain >= 1.0（`create_agent`）、langchain-openai、langchain-deepseek |
| 数据校验 | Pydantic v2、pydantic-settings |
| 鉴权 | PyJWT |
| HTTP 客户端 | httpx |
| 包管理 | uv |

---

## 核心设计

本项目在 LangChain 之上构建了一层 **Harness（工程骨架）**，把「可信」与「可控」从提示词层面下沉到工程层面。

### 1. 技能路由（渐进式披露）

不一次性把 9 个工具和全部领域说明交给模型，而是：

1. 先只提供一份精简的**领域索引**和一个 `load_skill` 工具
2. 模型判断领域后调用 `load_skill`，更新 `active_skill_code` 状态
3. 中间件按状态**收窄模型可见的工具集**，同时动态重建系统提示词

收益：提示词更短（降低 token 成本）、工具更少（提升选择准确率）、领域规则互相隔离（避免串话）。

### 2. 服务端事实校验（反幻觉）

不依赖模型自觉，而是等回复生成后**反向校验**：

1. 用正则从回复中抽取业务事实：编号（`ORDER_001`）、数字（金额/库存）、状态（已发货）
2. 从本次运行中**成功工具调用的入参与结果**递归展开，收集全部标量作为证据
3. 逐项比对，找不到出处的判定为编造，打回让模型重新生成

三个实现细节：
- 数字用 `Decimal` 比较，消除 `399` / `399.0` / `"399"` 的格式差异
- 文本用 `NFKC` 归一化，统一全角半角
- 状态做中文标签与服务端编码的**双向映射**（`已发货` ↔ `shipped`）

### 3. 页面动作白名单

模型不能直接返回链接，只能给出**动作编码 + 资源编号**；按钮文案与跳转链接全部由服务端模板生成，资源编号会做 URL 编码防注入。

若动作引用了某个订单，则要求该订单**必须在本次运行中被订单详情工具成功查询过**，保证生成的链接一定属于当前用户。

### 4. 输出纠错闭环

校验失败且错误属于「可纠正」类型时，保留本轮完整消息轨迹，仅追加一条说明错误原因的系统消息，让模型重新生成（上限 2 次）。

保留轨迹的原因：从零重来模型很可能重复犯错，它并不知道自己错在哪。

错误码按类型分为两类，只有可纠正的才重试：

| 类别 | 错误码 |
|---|---|
| 可纠正 | `MODEL_OUTPUT_INVALID`、`UNSUPPORTED_FACT`、`UNVERIFIED_ACTION_RESOURCE` |
| 终态 | `MODEL_CALL_FAILED`、`OUTPUT_VALIDATION_FAILED`、`AGENT_EXECUTION_FAILED` |

### 5. 工具调用两阶段写入

工具执行**前**先用独立会话写入一条调用记录并提交，执行完成后再回填结果与耗时。

好处：即使执行中途进程崩溃，数据库中也有「调用过什么」的痕迹；配合 `UniqueConstraint(run_id, tool_call_id)` 保证幂等。

### 6. 可观测性

每次运行的模型名、提示词版本、耗时、token 用量，以及每次工具调用的入参、出参、耗时，全部落库，并提供运营观测接口查询。

---

## 目录结构

```
atguigu/
├── main.py                      启动入口
├── common/                      公共层：配置、事件循环、工具函数
├── infrastructure/              基础设施层：数据库、下游 HTTP 客户端、建表脚本
├── models/                      数据模型层：AgentRun / AgentToolCall
├── app/                         Web 应用层
│   ├── app.py                   FastAPI 装配（路由 / lifespan / CORS）
│   ├── dependencies.py          依赖注入总装
│   ├── routers/                 内部业务接口 + 运营观测接口
│   ├── schemas/                 请求响应模型
│   ├── services/                鉴权服务、观测查询服务
│   └── repositories/            仓储层：AgentRun / AgentToolCall 持久化
└── agent/                       Agent 核心层
    ├── factory.py               Agent 装配
    ├── llm/                     模型适配、结构化输出契约、基础提示词
    └── harness/                 运行时骨架
        ├── dynamic_prompt.py    动态系统提示词
        ├── errors.py            错误码体系
        ├── knowledge/           知识查询（当前为 mock 实现）
        ├── rules/               页面动作目录、业务事实校验、纠错规则
        ├── skills/              技能定义、目录与工具收窄中间件
        ├── run/                 运行编排：上下文编译、协调器、执行器、输出映射、事件
        ├── tools/               工具目录、统一执行器、只读业务工具
        └── validator/           回答校验、页面动作校验
```

---

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

然后编辑 `.env`，填入数据库连接串与模型 API Key。

> 需要注意的配置项：
> - `LLM_BASE_URL` **没有默认值**，必须显式配置，否则启动即报错
> - `AI_DATABASE_URL` 的驱动必须是异步的（`postgresql+psycopg://`）
> - `JWT_SECRET` 必须与上游 customer-service 签发令牌所用密钥一致

### 3. 初始化数据库

```bash
python -m atguigu.infrastructure.init_db
```

### 4. 启动服务

```bash
python -m atguigu.main
```

默认监听 `0.0.0.0:8002`。

---

## 接口说明

### 内部业务接口

> 需携带 `X-Internal-Service-Token`，且用户角色须为 `customer`

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/internal/v1/agent/runs` | 发起一次 Agent 运行 |
| POST | `/internal/v1/agent/runs/{run_id}/confirm` | 确认两阶段决策 |
| POST | `/internal/v1/agent/runs/{run_id}/cancel` | 取消（返回 204） |

### 运营观测接口

> 用户角色须为 `admin`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/admin/metrics` | 汇总指标：运行总数、平均耗时、token 总量 |
| GET | `/api/v1/runs?limit=50` | 最近的运行列表 |
| GET | `/api/v1/runs/{run_id}` | 单次运行详情及其工具调用记录 |

---

## 平台兼容说明

在 Windows 上，asyncio 默认使用 `ProactorEventLoop`，而 psycopg 的异步实现依赖 `SelectorEventLoop` 提供的 socket 就绪机制，两者不兼容，会导致无法连接数据库。

本项目的处理方式是在 `common/event_loop.py` 中自建 `SelectorEventLoop`，并配合 Uvicorn 的 `loop="none"`（不让 Uvicorn 自行创建事件循环）。

---

## 已知待完善项

- `KnowledgeQueryService.search()` 目前返回固定数据，尚未接入真实检索
- `confirm_run` / `cancel_run` 未校验运行归属用户与当前状态
- 尚未提供测试用例
