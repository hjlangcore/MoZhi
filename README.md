# 墨智 MoZhi — AI 小说自动创作平台

> 基于 Ollama 本地大模型的 AI 小说创作系统，一键生成 50 万字原创长篇小说，自动分卷分章，适配番茄小说等平台发布。
> 前端水墨风格，写作管线集成 Agent Loop 动态调度、6道质量门禁、两阶段推理规划等主流技术方案。

## ✨ 核心能力

- **全自动写作** — AI 自动选题→设定→逐章创作→润色→校对→导出，全程无需人工干预
- **🌍 世界观构建系统** — 五要素框架：核心主题、历史脉络、社会结构、地理生态、物理规则，支持 **AI 一键自动生成**
- **👥 角色矩阵设计** — 完整角色设计模板：基础信息、核心矛盾、外在表现、成长弧线，支持 **AI 自动生成角色**
- **🎨 风格差异化策略** — 五维度风格选择：叙事视角、叙事节奏、语言风格、情感基调、主题深度，内置4种预设模板 + **AI 文风分析**
- **GPU+CPU 混合推理** — 自动检测显卡，RTX 3050 等入门级 GPU 也能流畅运行 7B 模型
- **自动分卷结构** — 50万字自动拆分为5卷，每卷约50章，导出文件自动插入卷标题
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
| **AI** | Ollama (qwen2.5:7b 推荐) |
| **GPU 加速** | CUDA (RTX 3050+), num_gpu=14 混合模式 |
| **核心架构** | Agent Loop、6道门禁、两阶段 REASONING→WRITING、Memory-First 动态记忆权重 |
| **前端** | React 18 + TypeScript + Vite + Zustand + Ant Design 5.x |
| **视觉风格** | 水墨风 — 宣纸色底、墨黑栏、朱砂红强调、宣纸纹理 |
| **存储** | JSON 文件持久化 (data/sessions.json + data/novels.json) |

## 快速开始

### 1. 安装 Ollama 并拉取模型

```bash
# 安装 Ollama: https://ollama.com

# Windows 启用 GPU 加速（推荐）
$env:OLLAMA_GPU="cuda"
ollama serve

# 推荐模型（7B，质量最佳）
ollama pull qwen2.5:7b      # 4.7GB，~60秒/章(GPU加速)
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
#   OLLAMA_TIMEOUT=300
```

### 4. 启动

```bash
# 终端1：后端 API
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：前端开发服务器
cd frontend && npm run dev
```

### 5. 使用

浏览器打开 `http://localhost:5173` →

**创作流程**：
1. 页面自动初始化默认写作会话
2. **「🌍 世界观构建」** → 设定五要素框架（支持 **✨ AI 自动生成** + 💾 保存）
3. **「👥 角色设计」** → 创建主角和配角（支持 **✨ AI 自动生成** + 💾 保存）
4. **「🎨 风格设定」** → 选择五维度风格（内置4种预设 + **✨ AI 文风分析** + 💾 保存）
5. **「📝 AI写作工坊」** → 「创建小说」→ 选择字数规模 → 点击「开始写作」
6. 实时观看：左侧章节列表自动刷新，右侧阅读正文
7. 完成后自动导出到 `novel_output/` 目录（含卷标头）

**风格预设模板**：
- 🍅 **番茄模式** — 快节奏爽文，适合网络小说平台
- 🧝 **修仙模式** — 古典仙侠风格，适合玄幻题材
- 🏙️ **都市模式** — 现实情感风格，适合都市题材
- 🏯 **明朝模式** — 历史爱情风格，专为古代言情定制

## 🤖 AI 生成功能

### 世界观自动生成

调用 `/api/v1/ai/generate/worldview` 接口，基于用户提示词自动生成完整的五要素世界观：

```
输入: "创建一个明朝背景的爱情小说世界观"
输出: {
  core_theme: "...",
  historical_events: [...],
  social_structure: { dominant_forces, class_divisions, core_conflicts },
  geography: { major_regions, power_distribution, key_locations },
  physics_rules: { power_system, limitations, cost_mechanism }
}
```

### 角色自动生成

调用 `/api/v1/ai/generate/character` 接口，基于世界观和角色类型自动生成详细角色卡：

```
输入: { role_type: "protagonist", world_context: {...} }
输出: {
  name, age, gender, social_identity,
  core_conflict, external_traits, growth_arc,
  relationships: [...]
}
```

### 文风分析

调用 `/api/v1/ai/generate/style-analysis` 接口，分析目标文本的文风特征并输出可复用的风格参数：

```
输入: { sample_text: "...", target_genre: "玄幻" }
输出: { narrative_viewpoint, pacing, language_style, emotional_tone, theme_depth }
```

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

## 模型推荐 & GPU 配置

| 显存 | 模型 | 大小 | 推理模式 | 速度(2000字) | 中文质量 |
|------|------|------|----------|--------------|--------|
| 4G (RTX 3050) | **qwen2.5:7b** | 4.7G | GPU+CPU混合(num_gpu=14) | ~60秒/章 | ★★★★★ |
| 8G | qwen2.5:7b | 4.7G | 全GPU | ~40-80秒/章 | ★★★★★ |
| 16G | qwen2.5:14b | 8.5G | 全GPU | ~60-120秒/章 | ★★★★★ |

> **GPU 加速启动方式**（Windows）：
> ```powershell
> $env:OLLAMA_GPU="cuda"
> ollama serve
> ```

## 项目结构

```
fusion-project/
├── src/
│   ├── api/                        # FastAPI 后端
│   │   ├── main.py                 # 应用入口 + 路由注册
│   │   ├── routes/
│   │   │   ├── ai_routes.py        # ✨ AI 生成接口（世界观/角色/文风）
│   │   │   ├── novel_routes.py     # 小说 CRUD + 世界观/角色/风格保存
│   │   │   ├── session_routes.py   # 会话管理
│   │   │   ├── chat_routes.py      # AI 对话
│   │   │   ├── writing_routes.py   # 自动写作控制
│   │   │   ├── network_routes.py   # 联网搜索 + 代理
│   │   │   └── ws_routes.py        # WebSocket 实时通信
│   │   └── schemas/                # Pydantic 数据模型
│   ├── core/
│   │   ├── config.py               # 配置管理 (.env)
│   │   ├── session_store.py        # JSON 文件持久化存储
│   │   ├── exceptions.py           # 异常体系
│   │   ├── retry.py                # 重试机制
│   │   ├── logging_config.py       # 日志设置（Windows 安全轮转）
│   │   ├── network_client.py       # HTTP 客户端
│   │   └── proxy_manager.py        # 代理管理
│   └── novel_agent/                # 核心 AI 创作引擎
│       ├── workflow.py             # 主编排管线（集成 25+ 模块）
│       ├── agent_loop.py           # Agent Loop 动态调度引擎
│       ├── generation_gates.py     # 6 道生成门禁
│       ├── reasoning_planner.py    # 两阶段推理规划
│       ├── enhanced_audit.py       # LLM 深度审计 + 趋势追踪
│       ├── state_writeback.py      # 状态回写 + 上下文压缩
│       ├── memory_weights.py       # 动态记忆权重 (Memory-First)
│       ├── story_planner.py        # 故事大纲规划（50万字 5 卷）
│       ├── rhythm_controller.py    # 节奏控制（张弛有度）
│       ├── coherence_manager.py    # 长篇连贯性管理
│       ├── card_system.py          # 角色 / 世界卡片系统
│       ├── style_analyzer.py       # 文风分析引擎
│       ├── prompts.py              # 专业 Prompt 模板库
│       ├── state.py                # 状态模型（含 world_view 字段）
│       ├── knowledge_integrator.py # 联网知识注入
│       ├── novel_exporter.py       # 小说导出（含卷标头）
│       └── ... (共 25+ 个模块)
├── frontend/
│   └── src/
│       ├── App.tsx                 # 主布局（水墨主题）
│       ├── index.css               # 水墨风格全局样式
│       ├── store.ts                # Zustand 全局状态管理
│       └── components/
│           ├── WorldBuildingPanel.tsx  # 🌍 世界观构建面板（AI 生成 + 保存）
│           ├── CharacterPanel.tsx      # 👥 角色设计面板（AI 生成 + 保存）
│           ├── StylePanel.tsx          # 🎨 风格设定面板（AI 分析 + 保存）
│           ├── NovelPanel.tsx          # 📝 AI 写作工坊
│           ├── SessionsPanel.tsx       # 会话管理
│           └── Sidebar.tsx             # 导航侧边栏
├── tests/                          # 单元测试
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 排除规则
├── requirements.txt                # Python 依赖
├── Dockerfile                      # Docker 构建文件
├── docker-compose.yml              # Docker 编排
├── Modelfile                       # Ollama 自定义模型 (3B)
├── Modelfile-7b                    # Ollama 自定义模型 (7B)
├── main.py                         # CLI 入口
└── run_api.py                      # API 启动脚本
```

## API 文档

启动后端后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 核心 API 端点

#### AI 生成接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/ai/generate/worldview` | AI 生成世界观（五要素框架） |
| POST | `/api/v1/ai/generate/character` | AI 生成角色卡片 |
| POST | `/api/v1/ai/generate/style-analysis` | AI 文风分析与提取 |

#### 数据保存接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/novels/{id}/worldview` | 保存世界观数据 |
| POST | `/api/v1/novels/{id}/characters` | 保存角色数据 |
| POST | `/api/v1/novels/{id}/style` | 保存风格设置 |

#### 小说与写作接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/sessions/` | 创建会话 |
| POST | `/api/v1/novels/` | 创建小说 |
| DELETE | `/api/v1/novels/{id}` | 删除小说/草稿 |
| GET | `/api/v1/novels/{id}/setting` | 获取小说设定 |
| POST | `/api/v1/writing/{id}/start` | 启动自动写作 |
| POST | `/api/v1/writing/{id}/stop` | 停止写作 |
| GET | `/api/v1/writing/{id}/status` | 查询写作进度 |
| GET | `/api/v1/novels/{id}/chapters` | 获取章节列表 |
| GET | `/api/v1/novels/{id}/chapters/{n}` | 获取章节内容 |
| POST | `/api/v1/chat/message` | 发送 AI 对话 |

## 写作参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| length_type | tomato | tomato(50万字)/short(3万)/mid(10万)/long(30万)/custom |
| chapter_words | 2200 | 每章字数（推荐 2000-2200 适配番茄） |
| custom_target_words | 0 | 自定义总字数 |

## Docker 部署

```bash
docker-compose up -d
# 访问 http://localhost:8000/docs
```

## 开发说明

### 环境要求
- Python 3.11+
- Node.js 18+
- Ollama (可选 GPU)

### 本地开发热重载
```bash
# 后端（自动重载代码变更）
python -m uvicorn src.api.main:app --reload

# 前端（Vite HMR）
cd frontend && npm run dev
```

## License

MIT
