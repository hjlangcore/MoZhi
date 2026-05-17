# Fusion Project — AI 小说自动创作平台

> 基于 Ollama 本地大模型的 AI 小说创作系统，一键生成 50 万字原创长篇小说，自动分卷分章，适配番茄小说等平台发布。
> 前端水墨风格，写作管线集成 Agent Loop 动态调度、6道质量门禁、两阶段推理规划等主流技术方案。

## 核心能力

- **全自动写作** — AI 自动选题→设定→逐章创作→润色→校对→导出，全程无需人工干预
- **世界观构建系统** — 五要素框架：核心主题、历史脉络、社会结构、地理生态、物理规则，支持 AI 自动生成
- **角色矩阵设计** — 完整角色设计模板：基础信息、核心矛盾、外在表现、成长弧线，支持主角/配角管理
- **风格差异化策略** — 五维度风格选择：叙事视角、叙事节奏、语言风格、情感基调、主题深度，内置4种预设模板
- **自动分卷结构** — 50万字自动拆分为5卷，每卷约50章，导出文件自动插入卷标题
- **原创角色体系** — 内置角色数量指南（核心主角1-3人、核心配角5-8人、辅助角色20-30人、背景角色50+），鼓励原创命名
- **Agent Loop 动态调度** — 每章写完后动态决策是否需要润色/校对/修正，质量不达标时自动迭代优化
- **6 道生成门禁** — 字数→钩子→连贯→类型→重复→AI痕迹，任何 FAIL 自动修正至通过
- **两阶段推理** — REASONING 深度分析剧情位置 → WRITING 基于规划执行创作
- **长篇保障** — 50万字+长篇连贯性管理，滚动摘要+角色追踪+伏笔回收+状态回写
- **实时观看** — 水墨风格 Web 前端实时展示写作进度，每章写出来就能立即阅读
- **本地运行** — 全部基于 Ollama 本地大模型，无需联网，隐私安全

## 技术栈

| 层 | 技术 |
|---|---|
| **后端** | FastAPI + Python 3.11 |
| **AI** | Ollama (qwen2.5:3b / 推荐 7b) |
| **核心架构** | Agent Loop、6道门禁、两阶段 REASONING→WRITING、Memory-First 动态记忆权重 |
| **前端** | React 18 + TypeScript + Vite + Zustand + Ant Design |
| **视觉风格** | 水墨风 — 宣纸色底、墨黑栏、朱砂红强调、宣纸纹理 |
| **存储** | JSON 文件持久化 (data/sessions.json + data/novels.json) |

## 快速开始

### 1. 安装 Ollama 并拉取模型

```bash
# 安装 Ollama: https://ollama.com
ollama serve

# 方案A：轻量快速
ollama pull qwen2.5:3b      # 1.9GB，30-60秒/章

# 方案B：高质量（推荐）
ollama pull qwen2.5:7b      # 4.7GB，60-120秒/章
```

### 2. 安装依赖

```bash
cd fusion-project
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 3. 配置

```bash
cp .env.example .env
# 编辑 .env，关键配置：
#   OLLAMA_BASE_URL=http://localhost:11434
#   OLLAMA_MODEL=qwen2.5:7b
```

### 4. 启动

```bash
# 终端1：后端
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 终端2：前端
cd frontend && npm run dev
```

### 5. 使用

浏览器打开 `http://localhost:5173` →

**创作流程**：
1. 页面自动初始化默认写作会话
2. **「世界观构建」** → 设定核心主题、历史脉络、社会结构、地理生态、物理规则（支持AI自动生成）
3. **「角色设计」** → 创建主角和配角，填写基础信息、核心矛盾、外在表现、成长弧线
4. **「风格设定」** → 选择叙事视角、节奏、语言风格、情感基调、主题深度（内置4种预设模板）
5. **「AI写作工坊」** → 「创建小说」→ 选择字数规模 → 点击「开始写作」
6. 实时观看：左侧章节列表自动刷新，右侧阅读正文
7. 完成后自动导出到 `novel_output/` 目录（含卷标头）

**风格预设模板**：
- 🍅 **番茄模式** — 快节奏爽文，适合网络小说平台
- 🧝 **修仙模式** — 古典仙侠风格，适合玄幻题材
- 🏙️ **都市模式** — 现实情感风格，适合都市题材
- 🏯 **明朝模式** — 历史爱情风格，专为古代言情定制

## 写作管线详情

```
每章执行流程：
Phase 1: 卷上下文注入 → 记忆权重计算 → 推理规划(REASONING) → 联网知识注入
Phase 2: 正文写作(WRITING) → 去AI痕迹 → 重复检查 → 风格验证
Phase 3: 6 道门禁检查 → 增强审计(每10章) → 状态回写
Phase 4: Agent Loop 动态调度 → 优化/修正/重写 → 下一章

每5章：连贯性检查 + 伏笔管理
每10章：多维度质量审计 + 趋势分析
每卷结束：自动插入卷标头（第X卷「卷名」）
```

## 分卷结构（50万字）

| 卷 | 标题 | 章节范围 | 核心目标 |
|----|------|---------|---------|
| 第1卷 | 觉醒启程卷 | 第1-50章 | 主角从平凡中觉醒，迈出改变命运的第一步 |
| 第2卷 | 立足扎根卷 | 第51-100章 | 在新环境中站稳脚跟，建立关系网络 |
| 第3卷 | 风云际会卷 | 第101-150章 | 参与更大格局博弈，建立声望 |
| 第4卷 | 生死考验卷 | 第151-200章 | 面对最大威胁，经历生死考验 |
| 第5卷 | 收官收束卷 | 第201-250章 | 收束所有伏笔，角色命运交代 |

## 角色数量指南（50万字）

| 角色类型 | 数量 | 说明 |
|----------|------|------|
| 核心主角 | 1-3人 | 贯穿全书，完整成长弧线 |
| 核心配角 | 5-8人 | 每个有独立故事线，与主角紧密关联 |
| 辅助角色 | 20-30人 | 服务于特定情节，阶段性出场 |
| 背景角色 | 50+ | 一笔带过或群体描写 |

## 番茄小说发布指南

| 字数节点 | 事件 | 说明 |
|----------|------|------|
| 2万字(10章) | 可申请签约 | AI 自动覆盖 |
| 8万字(36章) | 进入验证期 | AI 自动覆盖 |
| 10万字(45章) | 正式首秀 | AI 自动覆盖 |
| 30万字(136章) | 书测 | AI 自动覆盖 |
| 50万字(227章) | 长篇完结 | AI 自动覆盖 |

> 建议 AI 写完后人工审校一遍，加入个人风格细节。

## 模型推荐

| 显存 | 模型 | 大小 | 速度(2000字) | 中文质量 |
|------|------|------|--------------|--------|
| 4G | qwen2.5:3b | 1.9G | ~30-60秒/章 | ★★★ |
| 4G | **qwen2.5:7b** | 4.7G | ~60-120秒/章 | ★★★★★ |
| 8G | qwen2.5:7b | 4.7G | ~40-80秒/章 | ★★★★★ |
| 16G | qwen2.5:14b | 8.5G | ~60-120秒/章 | ★★★★★ |

## 项目结构

```
fusion-project/
├── src/
│   ├── api/                        # FastAPI 路由
│   │   ├── main.py                 # 应用入口
│   │   ├── routes/
│   │   │   ├── session_routes.py   # 会话管理
│   │   │   ├── novel_routes.py     # 小说CRUD
│   │   │   ├── chat_routes.py      # AI对话
│   │   │   ├── writing_routes.py   # 自动写作控制
│   │   │   ├── network_routes.py   # 联网搜索+代理
│   │   │   └── ws_routes.py        # WebSocket
│   │   └── schemas/                # Pydantic模型
│   ├── core/
│   │   ├── config.py               # 配置管理
│   │   ├── session_store.py        # 文件持久化存储
│   │   ├── exceptions.py           # 异常体系
│   │   ├── retry.py                # 重试机制
│   │   ├── logging_config.py       # 日志设置（Windows安全轮转）
│   │   ├── network_client.py       # HTTP客户端
│   │   └── proxy_manager.py        # 代理管理
│   └── novel_agent/                # 核心AI创作引擎
│       ├── workflow.py             # 主编排管线（集成20+模块）
│       ├── agent_loop.py           # Agent Loop 动态调度引擎
│       ├── generation_gates.py     # 6 道生成门禁
│       ├── reasoning_planner.py    # 两阶段推理规划
│       ├── enhanced_audit.py       # LLM深度审计+趋势追踪
│       ├── state_writeback.py      # 状态回写+上下文压缩
│       ├── memory_weights.py       # 动态记忆权重 (Memory-First)
│       ├── story_planner.py        # 故事大纲规划（50万字5卷+角色数量指南）
│       ├── rhythm_controller.py    # 节奏控制（张弛有度）
│       ├── coherence_manager.py    # 长篇连贯性管理
│       ├── card_system.py          # 角色/世界卡片系统
│       ├── prompts.py              # 专业Prompt模板
│       ├── state.py                # 状态模型（含VolumeModel分卷）
│       ├── knowledge_integrator.py # 联网知识注入
│       ├── novel_exporter.py       # 小说导出（含卷标头）
│       └── ... (共25个模块)
├── frontend/
│   └── src/
│       ├── App.tsx                 # 主布局（水墨主题，直接展示写作工坊）
│       ├── index.css               # 水墨风格全局样式
│       ├── store.ts                # Zustand全局状态
│       └── components/
│           ├── NovelPanel.tsx      # AI写作工坊（含小说删除功能）
│           ├── SessionsPanel.tsx   # 会话管理（后台保留）
│           └── Sidebar.tsx         # 侧边栏（后台保留）
├── novel_output/                   # 小说导出目录
├── data/                           # 会话/小说持久化数据
├── tests/                          # 单元测试
├── .env.example                    # 环境变量模板
├── requirements.txt                # Python依赖
├── Dockerfile
└── docker-compose.yml
```

## API 文档

启动后端后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 核心端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/sessions/` | 创建会话 |
| POST | `/api/v1/novels/` | 创建小说 |
| DELETE | `/api/v1/novels/{id}` | 删除小说/草稿 |
| POST | `/api/v1/writing/{id}/start` | 启动自动写作 |
| POST | `/api/v1/writing/{id}/stop` | 停止写作 |
| GET | `/api/v1/writing/{id}/status` | 查询写作进度 |
| GET | `/api/v1/novels/{id}/chapters` | 获取章节列表 |
| GET | `/api/v1/novels/{id}/chapters/{n}` | 获取章节内容 |
| POST | `/api/v1/chat/message` | 发送AI对话 |

## 写作参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| length_type | tomato | tomato(50万字)/short(3万)/mid(10万)/long(30万)/custom |
| chapter_words | 2200 | 每章字数（推荐2000-2200适配番茄） |
| custom_target_words | 0 | 自定义总字数 |

## 许可证

MIT
