# 🖋️ 墨智 (MoZhi) — AI 驱动的智能小说创作平台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18+-61DAFB.svg" alt="React" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
  <img src="https://img.shields.io/badge/Ollama-Supported-orange.svg" alt="Ollama" />
</p>

> **墨智** — 让 AI 成为你的创作伙伴，基于本地大模型的一站式小说自动生成系统。支持世界观构建、角色设计、章节生成、质量保障全流程自动化。

---

## ✨ 核心功能

| 功能模块 | 关键特性 |
|---------|---------|
| 🎨 **小说设定工坊** | 世界观五要素框架 / 角色矩阵设计 / 风格差异化策略（4种预设模板）|
| 🤖 **AI 智能生成** | 一键生成世界观 / 自动创建角色 / AI 文风分析 / 章节智能续写 |
| 📝 **多阶段写作管线** | REASONING 深度分析 → WRITING 创作执行 → Agent Loop 动态调度优化 |
| 🛡️ **质量保障体系** | 后处理5步清洗 / 一致性状态机 / 场景轮换器 / 智能标题去重 |
| 🔄 **长篇连贯性管理** | 滚动摘要 / 角色追踪 / 伏笔回收 / 状态回写（50万字+）|
| ⚡ **GPU 加速推理** | CUDA 混合模式 / RTX 3050+ 入门级显卡支持 / ~60秒/章 |
| 🖥️ **水墨风前端** | 实时写作进度展示 / 所见即所得编辑 / 多项目管理 |

### 🎯 质量保障四大防退化模块

| 问题类型 | 解决方案 | 效果 |
|---------|---------|------|
| 🔴 剧情原地打转（山洞循环）| 场景多样性轮换器（8种场景池 + FIFO队列）| 打破重复场景 |
| 🔴 里程碑重复达成 | 一致性状态机锁定机制 | 防止境界重复突破 |
| 🔴 元叙事泄露（AI指令写入正文）| 后处理管道过滤（5步清洗）| 移除残留指令 |
| 🟡 标题高度重复 | SequenceMatcher+Jaccard 双算法去重 | 确保标题唯一性 |

---

## 📑 目录导航

- [🚀 快速开始](#-快速开始)
- [📦 安装指南](#-安装指南)
- [⚙️ 配置说明](#-配置说明)
- [🎮 使用教程](#-使用教程)
- [🏗️ 项目架构](#-项目架构)
- [🔌 API 接口](#-api-接口)
- [🛡️ 质量保障体系详情](#-质量保障体系详情)
- [❓ 常见问题](#-常见问题)
- [📄 开源协议](#-开源协议)

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.10 或更高版本
- **Node.js**: 18 或更高版本（前端开发）
- **Ollama**: 本地 LLM 服务（[下载地址](https://ollama.com)）
- **GPU**: 推荐 NVIDIA 显卡（RTX 3050+，用于加速推理）

### 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/hjlangcore/fusion-project.git
cd fusion-project

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件（详见配置说明）

# 5. 启动 Ollama（启用 GPU 加速）
export OLLAMA_GPU=cuda  # Linux/Mac
# set OLLAMA_GPU=cuda   # Windows
ollama serve &

# 6. 拉取推荐模型
ollama pull qwen2.5:7b  # 4.7GB，质量与速度平衡

# 7. 启动服务
python run_api.py        # 后端 API (端口 8000)
cd frontend && npm run dev  # 前端开发服务器 (端口 5173)
```

### Docker 部署（可选）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

浏览器访问：`http://localhost:5173`

---

## 📦 安装指南

### Windows 用户

```powershell
# 1. 安装 Python 3.10+
# 下载地址：https://www.python.org/downloads/

# 2. 安装 Ollama
# 下载地址：https://ollama.com/download/windows

# 3. 启用 GPU 加速（PowerShell）
$env:OLLAMA_GPU = "cuda"
ollama serve

# 4. 克隆并安装
git clone https://github.com/hjlangcore/fusion-project.git
cd fusion-project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd frontend; npm install; cd ..

# 5. 运行
python run_api.py
```

### Linux/Mac 用户

```bash
# 1. 安装系统依赖（Ubuntu/Debian）
sudo apt update
sudo apt install python3 python3-pip nodejs npm

# 2. 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. 启用 GPU 加速
export OLLAMA_GPU=cuda
ollama serve &

# 4. 克隆并安装
git clone https://github.com/hjlangcore/fusion-project.git
cd fusion-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 5. 运行
python3 run_api.py
```

---

## ⚙️ 配置说明

### 环境变量 (.env)

```bash
# ============ API 配置 ============
API_HOST=0.0.0.0          # 监听地址
API_PORT=8000             # 监听端口
DEBUG=false               # 调试模式

# ============ Ollama LLM 配置 ============
OLLAMA_HOST=http://localhost:11434  # Ollama 服务地址
OLLAMA_MODEL=qwen2.5:7b            # 推荐模型（7B 参数量）
OLLAMA_TIMEOUT=300                  # 请求超时时间（秒）

# ============ GPU 加速配置 ============
OLLAMA_GPU=cuda            # 启用 CUDA GPU 加速（推荐）

# ============ 数据库配置 ============
DATABASE_URL=sqlite:///./data/novels.db  # SQLite 数据库路径

# ============ AI 生成参数 ============
MAX_TOKENS=4096            # 最大生成 token 数
TEMPERATURE=0.7            # 温度参数（0-1，越高越有创意）
TOP_P=0.9                 # Top-P 采样参数

# ============ 质量保障配置 ============
QUALITY_ENABLED=true                    # 启用质量保障体系
POSTPROCESSOR_ENABLED=true              # 启用后处理管道
CONSISTENCY_TRACKER_ENABLED=true        # 启用一致性状态机
SCENE_ROTATOR_ENABLED=true              # 启用场景轮换器
TITLE_MANAGER_ENABLED=true              # 启用标题去重
SIMILARITY_THRESHOLD=0.55              # 标题相似度阈值
SCENE_HISTORY_SIZE=10                  # 场景历史记录大小
SCENE_WARNING_THRESHOLD=3              # 场景连续同类警告阈值
SCENE_FORCE_SWITCH_LIMIT=5             # 场景强制切换上限
```

### 推荐模型对比

| 模型名称 | 参数量 | 大小 | 推理速度（GPU）| 质量 | 适用场景 |
|---------|-------|------|---------------|------|---------|
| `qwen2.5:7b` | 7B | 4.7GB | ~60秒/章 | ⭐⭐⭐⭐⭐ | **推荐**，质量最佳 |
| `qwen2.5:3b` | 3B | 2.1GB | ~35秒/章 | ⭐⭐⭐⭐ | 快速生成，资源有限时使用 |
| `llama3:8b` | 8B | 4.7GB | ~65秒/章 | ⭐⭐⭐⭐ | 英文内容优先 |
| `deepseek-v2:16b` | 16B | 10GB | ~120秒/章 | ⭐⭐⭐⭐⭐ | 高质量长文本 |

---

## 🎮 使用教程

### 第一步：创建项目

1. 打开浏览器访问 `http://localhost:5173`
2. 点击「新建项目」按钮
3. 选择小说类型：修真 / 玄幻 / 科幻 / 都市 / 历史
4. 填写基本信息：
   - 书名（如：《星辰变》）
   - 作者笔名
   - 简介（一句话概括故事核心）
5. 点击「确认创建」

### 第二步：构建世界观

**方式 A：手动设定**
1. 进入「世界观构建」页面
2. 填写五要素：
   - **核心主题**：修炼体系、力量来源
   - **历史脉络**：重要历史事件时间线
   - **社会结构**：宗门、帝国、势力分布
   - **地理生态**：大陆地图、特殊地域
   - **物理规则**：魔法/科技规则
3. 点击「保存设定」

**方式 B：AI 自动生成（推荐）✨**
1. 在「世界观构建」页面点击「✨ AI 生成」
2. 等待 30-60 秒（GPU 加速）
3. 审查生成的世界观
4. 可手动调整后保存

### 第三步：设计角色

1. 进入「角色设计」页面
2. 点击「添加角色」

**手动创建**：
- 填写基础信息：姓名、性别、年龄、出身
- 设定核心矛盾：内心冲突、外部冲突
- 描述外在表现：性格特征、行为习惯
- 规划成长弧线：起始状态→转折点→最终状态

**AI 自动生成 ✨**：
- 选择角色类型：主角 / 配角 / 反派
- 点击「✨ AI 生成角色」
- AI 会根据世界观自动生成合适角色

### 第四步：设定文风

1. 进入「风格设定」页面
2. 选择五维度风格：

| 维度 | 选项示例 |
|------|---------|
| 叙事视角 | 第一人称 / 第三人称有限 / 第三人称全知 |
| 叙事节奏 | 快节奏（爽文）/ 中速（传统）/ 慢节奏（文学）|
| 语言风格 | 古风典雅 / 现代白话 / 网文口语化 |
| 情感基调 | 轻松幽默 / 热血激昂 / 深沉厚重 |
| 主题深度 | 娱乐向 / 思辨向 / 哲学向 |

3. **预设模板快速选择**：
   - 🍅 **番茄模式** — 快节奏爽文，适合网络小说平台
   - 🧝 **修仙模式** — 古典仙侠风格，适合玄幻题材
   - 🏙️ **都市模式** — 现实情感风格，适合都市题材
   - 🏯 **明朝模式** — 历史爱情风格，专为古代言情定制

4. **AI 文风分析 ✨**：上传参考文本，AI 分析并模仿其文风
5. 点击「保存风格」

### 第五步：开始写作

1. 进入「AI 写作工坊」页面
2. 点击「创建小说」
3. 设置参数：
   - **总字数规模**：10万字 / 30万字 / 50万字 / 自定义
   - **每章字数**：2000-5000 字（建议 3000）
   - **卷数设置**：自动计算或手动指定
4. 点击「🚀 开始写作」

### 第六步：实时监控与导出

**实时观看**：
- 左侧面板：章节列表（实时更新）
- 右侧面板：正文阅读区（每章完成后立即可读）
- 底部状态栏：当前进度、已写字数、预计剩余时间

**导出作品**：
1. 写作完成后，点击「导出」按钮
2. 选择格式：TXT / EPUB / PDF
3. 选择范围：全部章节 / 指定卷 / 指定章节范围
4. 导出文件保存到 `novel_output/` 目录

**输出文件结构**：
```
novel_output/
├── 《书名》_完整版.txt      # 全文合并
├── 卷一_《卷标题》/
│   ├── 第001章_章节名.txt
│   ├── 第002章_章节名.txt
│   └── ...
├── 卷二_《卷标题》/
│   └── ...
└── metadata.json           # 元数据（字数统计、章节信息等）
```

---

## 🏗️ 项目架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 18)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Dashboard│ │ Editor   │ │ Config   │ │ Data Manager │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       └────────────┴────────────┴──────────────┘           │
│                           │                                │
│                    Axios / REST API                         │
└───────────────────────────┼───────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────┐
│                     Backend (FastAPI)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ API Routes│ │ Novel    │ │ AI       │ │ Quality      │  │
│  │          │ │ Engine   │ │ Service  │ │ Modules      │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       └────────────┴────────────┴──────────────┘           │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │              Business Logic Layer                │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌────────────┐  │     │
│  │  │ Postprocessor│ │ Consistency │ │ Scene      │  │     │
│  │  │ Pipeline     │ │ Tracker     │ │ Rotator    │  │     │
│  │  └─────────────┘ └─────────────┘ └────────────┘  │     │
│  └──────────────────────────────────────────────────┘     │
└───────────────────────────┼───────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────┐
│                   Infrastructure Layer                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Ollama   │ │ SQLite   │ │ File     │ │ State        │  │
│  │ LLM      │ │ Database │ │ Storage  │ │ Management   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### 写作管线流程

```
用户请求生成第 N 章
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 0: 质量约束预加载                                      │
│ ├─ 一致性状态机查询（角色卡锁、里程碑锁定、伏笔状态）          │
│ ├─ 场景轮换器选择（8种场景池 + FIFO历史队列）                 │
│ └─ 标题去重检查（SequenceMatcher+Jaccard 双算法）             │
├─────────────────────────────────────────────────────────────┤
│ Phase 1: 上下文构建                                          │
│ ├─ 卷上下文注入（卷概述 + 前3章摘要）                          │
│ ├─ 记忆权重计算（近期高权重 + 关键事件加权）                   │
│ ├─ REASONING 深度分析（前文伏笔/冲突/节奏）                   │
│ └─ 联网知识注入（可选）                                       │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: 正文写作(WRITING)                                   │
│ ├─ 注入反退化Prompt（场景约束 + 一致性约束 + 质量要求）         │
│ ├─ LLM 生成正文（Ollama + GPU 加速）                         │
│ └─ 后处理管道清洗(5步)：                                      │
│    ├─ Step 1: 元叙事泄露过滤                                 │
│    ├─ Step 2: Markdown残留清理                               │
│    ├─ Step 3: AI痕迹词降频                                  │
│    ├─ Step 4: 章节号校验                                    │
│    └─ Step 5: 字数范围检查                                  │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: 质量门禁                                            │
│ ├─ 6道门禁检查（空内容/超短/纯对话/无进展/重复/退化）          │
│ ├─ 增强审计（每10章触发：一致性/连贯性/节奏/文风）              │
│ └─ 状态回写 + 状态机更新                                     │
├─────────────────────────────────────────────────────────────┤
│ Phase 4: Agent Loop 动态调度                                 │
│ ├─ 质量评分 → 自动决策（通过/优化/修正/重写）                  │
│ ├─ 迭代优化（最多3轮）                                        │
│ └─ 下一章准备                                                │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| **前端框架** | React 18 + TypeScript | 现代化前端开发 |
| **UI 组件库** | Ant Design 5.x | 企业级 UI 组件 |
| **状态管理** | Zustand | 轻量级状态管理 |
| **构建工具** | Vite | 极速前端构建 |
| **后端框架** | FastAPI | 高性能异步 Web 框架 |
| **AI 引擎** | Ollama + Qwen2.5/Llama3 | 本地 LLM 推理 |
| **数据库** | SQLite | 轻量级关系型数据库 |
| **数据验证** | Pydantic V2 | 数据模型验证 |
| **HTTP 客户端** | Axios | 前端 HTTP 请求 |
| **质量保障** | 4大防退化模块 | 后处理管道/一致性状态机/场景轮换器/标题去重 |

### 项目目录结构

```
fusion_project/
├── README.md                        # 项目文档（本文件）
├── requirements.txt                 # Python 依赖
├── package.json                     # Node.js 配置
├── docker-compose.yml               # Docker 编排
├── .env.example                     # 环境变量示例
├── .gitignore                       # Git 忽略规则
│
├── src/                            # 源代码目录
│   ├── api/                        # API 层
│   │   ├── main.py                 # FastAPI 应用入口
│   │   ├── dependencies.py         # 依赖注入
│   │   └── routes/                 # API 路由
│   │       ├── novel_routes.py     # 小说 CRUD 接口
│   │       ├── ai_routes.py        # AI 生成接口
│   │       └── character_routes.py # 角色管理接口
│   │
│   ├── models/                     # 数据模型
│   │   ├── novel.py                # 小说模型
│   │   ├── character.py            # 角色模型
│   │   └── chapter.py              # 章节模型
│   │
│   ├── services/                   # 业务服务层
│   │   ├── novel_service.py        # 小说业务逻辑
│   │   └── ai_service.py           # AI 调用服务
│   │
│   └── novel_agent/                # 核心 AI 创作引擎
│       ├── agent_loop.py           # Agent Loop 动态调度
│       ├── prompts.py              # Prompt 模板管理
│       ├── state.py                # 全局状态管理
│       ├── postprocessor.py        # 🧹 后处理过滤管道（5步清洗）
│       ├── consistency_tracker.py  # 🔒 一致性状态机
│       ├── scene_rotator.py        # 🔄 场景多样性轮换器
│       └── title_manager.py        # 🏷️ 智能标题去重服务
│
├── frontend/                      # 前端应用
│   ├── src/
│   │   ├── components/            # React 组件
│   │   ├── pages/                 # 页面组件
│   │   ├── store/                 # Zustand 状态管理
│   │   ├── services/              # API 服务
│   │   └── utils/                 # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
├── data/                          # 数据目录（Git 忽略）
├── novel_output/                  # 输出目录（Git 忽略）
└── tests/                         # 测试目录
    ├── test_api.py
    ├── test_ai_service.py
    └── test_quality_modules.py
```

---

## 🔌 API 接口

### 核心接口列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/novels` | 创建小说项目 | 无 |
| GET | `/api/v1/novels` | 获取小说列表 | 无 |
| GET | `/api/v1/novels/{id}` | 获取小说详情 | 无 |
| PUT | `/api/v1/novels/{id}` | 更新小说信息 | 无 |
| DELETE | `/api/v1/novels/{id}` | 删除小说项目 | 无 |
| POST | `/api/v1/ai/generate/worldview` | 生成世界观 | 无 |
| POST | `/api/v1/ai/generate/characters` | 生成角色 | 无 |
| POST | `/api/v1/ai/generate/chapter` | 生成章节 | 无 |
| POST | `/api/v1/ai/analyze/style` | 分析文风 | 无 |

### 使用示例

#### 生成世界观

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate/worldview \
  -H "Content-Type: application/json" \
  -d '{
    "novel_type": "修真",
    "genre": "东方玄幻",
    "custom_requirements": "强调修炼体系和宗门势力"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "worldview": {
      "core_theme": "以灵气为核心的修真世界...",
      "history_timeline": ["远古时期...", "上古大战..."],
      "social_structure": {"宗门": ["青云门", "天剑宗"]},
      "geography_ecology": {"continents": ["玄天大陆"]},
      "physics_rules": {"cultivation_system": "炼气→筑基→金丹..."}
    }
  },
  "message": "世界观生成成功"
}
```

#### 生成章节

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate/chapter \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "uuid-here",
    "chapter_number": 1,
    "target_words": 3000,
    "style_requirements": "紧凑节奏，注重战斗描写"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "chapter_number": 1,
    "title": "第一章 少年觉醒",
    "content": "在青云宗的山脚下...",
    "word_count": 3256,
    "quality_score": 92,
    "postprocessing_applied": [
      "元叙事泄露过滤",
      "Markdown残留清理",
      "AI痕迹词降频",
      "章节号校验",
      "字数范围检查"
    ]
  },
  "message": "章节生成成功"
}
```

### API 文档

启动服务后访问：`http://localhost:8000/docs` （Swagger UI）

---

## 🛡️ 质量保障体系详情

### 1️⃣ 后处理质量管道 (`postprocessor.py`)

**功能**: 5步自动清洗，确保输出质量

**处理流程**:

1. **元叙事泄露过滤**
   - 移除 "请按照以下要求"、"注意不要" 等 AI 指令残留
   - 正则匹配常见指令模式
   - 准确率 > 95%

2. **Markdown 残留清理**
   - 移除 `##`、`**`、`*`、`>` 等 Markdown 格式标记
   - 保留正文语义完整性

3. **AI 痕迹词降频**
   - 降低 "突然"、"竟然"、"居然"、"不禁" 等 AI 高频词
   - 同义词替换策略
   - 目标频率：< 3次/千字

4. **章节号校验**
   - 确保章节编号正确且连续
   - 自动修复编号错误

5. **字数范围检查**
   - 确保字数在用户要求的范围内（±10%容差）
   - 不达标时触发 Agent Loop 补充

**代码示例**:
```python
from src.novel_agent.postprocessor import PostProcessor

postprocessor = PostProcessor()
cleaned_text, report = postprocessor.process(
    raw_text=raw_chapter_content,
    chapter_num=5,
    target_words=3000
)

print(f"清洗完成！原始字数: {report['original_words']}, 清洗后: {report['cleaned_words']}")
print(f"应用的处理步骤: {report['applied_steps']}")
```

---

### 2️⃣ 一致性状态机 (`consistency_tracker.py`)

**功能**: 维护角色、里程碑、伏笔的一致性，防止剧情矛盾

**核心特性**:

- **角色卡锁**: 角色一旦创建，核心属性不可变（姓名、性别、出身）
- **里程碑锁定**: 里程碑只能达成一次，防止重复突破境界
- **反派状态管理**: 反派死亡后不可复活（除非有明确伏笔）
- **伏笔全生命周期追踪**: 埋设 → 提醒 → 回收 → 完成

**数据结构**:
```python
class ConsistencyTracker:
    characters: Dict[str, CharacterLock]      # 角色锁
    milestones: Dict[str, MilestoneStatus]    # 里程碑状态
    antagonists: Dict[str, AntagonistState]   # 反派状态
    foreshadowing: List[ForeshadowItem]       # 伏笔列表
```

**代码示例**:
```python
from src.novel_agent.consistency_tracker import ConsistencyTracker

tracker = ConsistencyTracker()

# 锁定角色核心属性
tracker.lock_character("张三", {
    "name": "张三",
    "gender": "男",
    "origin": "青云门",
    "core_traits": ["坚韧", "正义"]
})

# 达成里程碑（只能达成一次）
success = tracker.achieve_milestone(
    name="突破炼气期",
    chapter=10,
    description="张三成功突破到炼气期三层"
)
if not success:
    print("该里程碑已经达成过！")

# 埋设伏笔
tracker.add_foreshadowing(
    id="foreshadow_001",
    description="主角身上的神秘玉佩会在关键时刻发光",
    trigger_chapter=15,
    resolve_chapter=30,
    status="pending"
)

# 检查伏笔是否应该提醒
reminders = tracker.check_foreshadowing_reminders(current_chapter=14)
for item in reminders:
    print(f"⚠️ 请在第 {item.trigger_chapter} 章回收伏笔: {item.description}")
```

---

### 3️⃣ 场景多样性轮换器 (`scene_rotator.py`)

**功能**: 避免场景重复，确保剧情多样性，打破"山洞循环"

**8种场景池**:

| 编号 | 场景类型 | 说明 | 典型情节 |
|-----|---------|------|---------|
| 1 | 战斗场景 | 对抗、竞技、厮杀 | 决斗、团战、狩猎 |
| 2 | 探索场景 | 发现、冒险、寻宝 | 洞穴探索、遗迹发掘 |
| 3 | 修炼场景 | 提升、突破、领悟 | 闭关、炼丹、炼器 |
| 4 | 社交场景 | 交流、交易、结盟 | 宗门聚会、拍卖会 |
| 5 | 购物/交易场景 | 购买、出售、交换 | 丹药铺、武器店 |
| 6 | 调查/解谜场景 | 推理、追踪、破解 | 悬案调查、谜题解开 |
| 7 | 逃亡/追逐场景 | 奔跑、躲避、追击 | 被追杀、逃离险境 |
| 8 | 休息/日常场景 | 放松、情感、日常 | 朋友聊天、日常训练 |

**工作原理**:

1. **FIFO 历史队列**: 记录最近 N 个场景（默认 10 个）
2. **连续同类警告**: 连续 3 个同类场景时发出警告
3. **强制切换机制**: 连续同类超过上限（默认 5 个）时强制选择其他场景

**代码示例**:
```python
from src.novel_agent.scene_rotator import SceneRotator

rotator = SceneRotator(
    history_size=10,      # 记录最近10个场景
    warning_threshold=3,  # 连续3个同类场景时警告
    force_switch_limit=5  # 连续5个同类时强制切换
)

# 选择下一个场景
next_scene = rotator.select_next_scene(current_context={
    "previous_chapters": [...],
    "plot_requirements": "需要一场战斗来推动剧情"
})

if next_scene.warning:
    print(f"⚠️ 警告：连续{next_scene.consecutive_count}个{next_scene.scene_type}场景")

if next_scene.forced_switch:
    print(f"🔄 强制切换：从{next_scene.original_scene}切换到{next_scene.scene_type}")

print(f"建议场景类型: {next_scene.scene_type}")
```

---

### 4️⃣ 智能标题去重 (`title_manager.py`)

**功能**: 确保章节标题唯一性和多样性，避免高度重复

**双算法检测**:

1. **SequenceMatcher** (difflib)
   - 基于最长公共子序列的相似度
   - 适合检测顺序相似的标题

2. **Jaccard 相似度**
   - 基于词汇集合的相似度
   - 适合检测词汇重叠的标题

**最终相似度**: `max(sequence_similarity, jaccard_similarity)`

**4种变换策略**（当检测到重复时自动应用）:

| 策略 | 示例 | 适用场景 |
|------|------|---------|
| 同义词替换 | "神秘机关" → "古老机关" | 词汇层面重复 |
| 语序调整 | "机关启动" → "启动的机关" | 结构层面重复 |
| 细节添加 | "机关启动" → "机关再次启动" | 需要区分版本 |
| 语义重写 | "机关启动" → "暗藏的机关显露真容" | 高度重复时使用 |

**代码示例**:
```python
from src.novel_agent.title_manager import TitleManager

manager = TitleManager(similarity_threshold=0.55)

# 检查标题是否重复
is_unique, result = manager.check_and_generate("神秘机关启动")

if not is_unique:
    print(f"❌ 标题重复（相似度: {result.similarity:.2f}）")
    print(f"💡 建议使用的替代标题:")
    for i, suggestion in enumerate(result.suggestions, 1):
        print(f"   {i}. {suggestion.title} (策略: {suggestion.strategy})")
    
    # 使用第一个建议
    final_title = result.suggestions[0].title
else:
    print(f"✅ 标题唯一")
    final_title = "神秘机关启动"

# 注册标题（章节保存后调用）
manager.register_title(final_title, chapter_num=15)
```

---

## ❓ 常见问题

### Q1: 推理速度太慢怎么办？

**A**: 
1. ✅ 确保启用了 GPU 加速：`export OLLAMA_GPU=cuda`
2. ✅ 使用更小的模型：`qwen2.5:3b`（速度快 50%）
3. ✅ 减少 `MAX_TOKENS` 和目标字数
4. ✅ 检查 GPU 显存使用情况：`nvidia-smi`

### Q2: 生成的质量不理想？

**A**:
1. ✅ 调整 `TEMPERATURE` 参数（0.5-0.8 之间尝试）
2. ✅ 优化 Prompt 模板（修改 `src/novel_agent/prompts.py`）
3. ✅ 使用更大的模型（`qwen2.5:7b` 或 `qwen2.5:14b`）
4. ✅ 增加上下文长度（提供更多前文摘要）
5. ✅ 手动调整后处理管道参数

### Q3: 如何添加自定义风格模板？

**A**:
编辑 `src/novel_agent/prompts.py`，在 `STYLE_PRESETS` 字典中添加新模板：

```python
STYLE_PRESETS["custom"] = {
    "narrative_viewpoint": "第三人称有限",
    "pacing": "中速",
    "language_style": "你的自定义描述",
    "emotional_tone": "轻松幽默",
    "theme_depth": "娱乐向",
    "special_instructions": "额外要求..."
}
```

### Q4: 出现 "Connection refused" 错误？

**A**:
1. ✅ 检查 Ollama 是否运行：`ollama list`
2. ✅ 检查 `.env` 中 `OLLAMA_HOST` 是否正确
3. ✅ 重启 Ollama 服务：`ollama serve`
4. ✅ 检查防火墙是否阻止了 11434 端口

### Q5: 如何导出到其他平台（如番茄小说）？

**A**:
目前支持 TXT/EPUB/PDF 格式导出。如需番茄小说专用格式：
1. 导出为 TXT 格式
2. 使用在线转换工具或脚本转换为平台要求的格式
3. 未来计划直接支持更多平台格式

### Q6: 内存占用过高？

**A**:
1. ✅ 使用更小的模型（3B vs 7B）
2. ✅ 减少 `--reload` 监控目录范围
3. ✅ 增加 Python GC 频率
4. ✅ 使用 Docker 限制内存：`docker-compose.yml` 中添加 `mem_limit`

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试模块
pytest tests/test_api.py -v              # API 测试
pytest tests/test_ai_service.py -v       # AI 服务测试
pytest tests/test_quality_modules.py -v  # 质量模块测试

# 运行单个测试函数
pytest tests/test_quality_modules.py::TestPostProcessor::test_meta_filter -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
# 查看 htmlcov/index.html
```

---

## 📈 性能优化

### 已实施的优化

- ✅ **GPU 加速** — Ollama CUDA 推理，速度提升 5-10 倍
- ✅ **异步处理** — FastAPI async/await 支持
- ✅ **连接池** — 数据库连接复用
- ✅ **缓存机制** — 常用数据内存缓存
- ✅ **流式输出** — SSE 流式返回生成内容
- ✅ **质量管道并行化** — 后处理 5 步并行执行
- ✅ **状态机高效查询** — O(1) 时间复杂度的状态查询

### 进一步优化方向

- [ ] Redis 缓存层
- [ ] 模型量化（INT8/INT4）
- [ ] 批量推理优化
- [ ] 分布式部署
- [ ] 模型热加载

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- **Python**: 遵循 PEP 8，使用 Black 格式化
- **TypeScript**: 遵循 ESLint + Prettier
- **提交信息**: 遵循 Conventional Commits（`feat:`, `fix:`, `docs:` 等）
- **测试**: 新功能必须包含单元测试

### 开发流程示例

```bash
# 1. Fork 并克隆
git clone https://github.com/your-username/fusion-project.git
cd fusion-project

# 2. 创建分支
git checkout -b feature/add-new-quality-check

# 3. 开发并测试
# ... 编写代码 ...
pytest tests/ -v

# 4. 提交更改
git add .
git commit -m "feat: add repetition detection quality check"

# 5. 推送并创建 PR
git push origin feature/add-new-quality-check
# 在 GitHub 创建 Pull Request
```

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

```
MIT License

Copyright (c) 2024-2025 MoZhi Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 致谢

- [Ollama](https://ollama.ai/) — 本地 LLM 推理引擎
- [FastAPI](https://fastapi.tiangolo.com/) — 现代 Web 框架
- [React](https://reactjs.org/) — 前端 UI 框架
- [Ant Design](https://ant.design/) — 企业级 UI 组件库
- [Zustand](https://github.com/pmndrs/zustand) — 状态管理方案
- [Qwen2.5](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) — 强大的中文语言模型

---

## 📞 联系方式

- **项目地址**: [https://github.com/hjlangcore/fusion-project](https://github.com/hjlangcore/fusion-project)
- **问题反馈**: [Issues](https://github.com/hjlangcore/fusion-project/issues) — Bug 报告和功能请求
- **讨论交流**: [Discussions](https://github.com/hjlangcore/fusion-project/discussions) — 使用经验和技术讨论
- **邮箱**: [your-email@example.com](mailto:your-email@example.com)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

**让 AI 赋能创作，让想象力自由飞翔 🚀**

Made with ❤️ by [墨智团队](https://github.com/hjlangcore)

</div>
