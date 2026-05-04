# LaunchPad — 企业智能需求分析与项目立项 Agent 系统

## 一、项目介绍

### 1.1 项目简介

LaunchPad 是一个基于多 Agent 协作的智能系统，能够将业务人员的模糊需求描述自动转化为标准立项文档。系统通过多个专业化 Agent 的协同工作，在数小时内完成传统需要 2~4 周的需求分析到立项流程。

**核心输出物**：符合标准格式的立项文档（Word），包含可行性评估、资源评估、风险评估三个维度的完整分析。

**目标用户**：
- **业务人员**（需求提出方）：只需用自然语言描述需求，系统引导澄清细节
- **产品/研发负责人**（评审方）：在关键节点介入审核，最终确认立项决策

### 1.2 项目解决的核心痛点

| 痛点 | 传统方式 | LaunchPad 方案 |
|------|----------|----------------|
| 需求描述模糊 | 多次开会对齐，沟通成本高 | 多轮智能对话，自动追问缺失信息 |
| 评估维度遗漏 | 依赖个人经验，容易顾此失彼 | 可行性/资源/风险三维并行评估，自动交叉检查 |
| 历史经验难复用 | 靠记忆和口碑，新项目从零开始 | 向量检索历史相似项目，数据驱动决策 |
| 决策不透明 | 结论缺乏推理过程，事后难以追溯 | 五步推理链全程可视化，每步可审查 |
| 文档编写耗时 | 人工撰写，反复修改 | 一键生成标准立项文档，附免责声明 |

### 1.3 核心逻辑流

```
业务人员输入需求 → 需求澄清(多轮对话) → 任务拆解 → 三维并行分析 → 长链推理 → 人工审核 → 生成文档
```

**关键特性**：

- **多 Agent 协作**：8 个专业 Agent 分工协作，各司其职
- **并行分析**：可行性、资源、风险三个 Agent 同时运行，互不阻塞
- **长链推理**：综合 Agent 严格按五步推理链输出（汇总 → 冲突识别 → 路径推演 → 决策 → 输出），每步结果实时可见
- **人工审核嵌入**：置信度不足 0.7 的判断自动暂停，等待人工确认
- **推理可追溯**：侧边栏实时展示推理过程，决策透明可审计

详细架构说明见 [docs/agent_architecture.md](docs/agent_architecture.md)，推理规范见 [docs/reasoning_chain.md](docs/reasoning_chain.md)。

---

## 二、运行教程

> 本教程面向完全没有编程经验的用户。按照步骤操作即可在您的电脑上运行 LaunchPad。

### 步骤概览

```
安装基础软件 → 下载项目 → 配置密钥 → 初始化数据库 → 导入历史数据 → 启动系统 → 开始使用
```

---

### 步骤 1：安装 Python

Python 是本系统的运行环境。

1. 打开浏览器，访问 Python 官方下载页面：https://www.python.org/downloads/
2. 点击黄色按钮 **"Download Python 3.11.x"**（或更高版本）下载安装包
3. 双击下载的安装包，**务必勾选 "Add Python to PATH"**（将 Python 添加到系统路径），然后点击 "Install Now"
4. 安装完成后，验证是否成功：
   - 按下键盘 `Win + R`，输入 `cmd`，回车打开命令提示符
   - 输入 `python --version`，回车
   - 如果看到 `Python 3.11.x` 或更高版本，说明安装成功

### 步骤 2：安装 Node.js

Node.js 用于运行前端界面。

1. 打开浏览器，访问：https://nodejs.org/
2. 点击左侧 **LTS**（长期支持版）下载安装包（推荐 20.x 或更高版本）
3. 双击下载的安装包，一路点击 "Next" 完成安装
4. 验证安装：
   - 打开命令提示符（`Win + R`，输入 `cmd`）
   - 输入 `node --version`，回车
   - 输入 `npm --version`，回车
   - 如果都显示版本号，说明安装成功

### 步骤 3：安装 Git（用于下载项目）

1. 打开浏览器，访问：https://git-scm.com/download/win
2. 下载会自动开始，双击安装包
3. 安装过程中，所有选项保持默认，一路点击 "Next" 完成

### 步骤 4：下载项目到本地

1. 在您想要存放项目的文件夹（例如桌面）中右键，选择 **"Git Bash Here"**
2. 在弹出的命令行窗口中输入以下命令并回车：

   ```
   git clone https://github.com/anomalyco/launchpad.git
   ```

   如果没有 Git Bash，也可以打开普通命令提示符（`Win + R`，输入 `cmd`），先切换到目标文件夹，再执行上述命令。

3. 等待下载完成，文件夹中会出现一个 `launchpad` 目录

### 步骤 5：安装项目依赖

1. 打开命令提示符（`Win + R`，输入 `cmd`，回车）
2. 进入项目目录（假设项目在桌面上）：

   ```
   cd Desktop\launchpad
   ```

3. 安装 Python 依赖（复制以下命令，粘贴到命令行，回车）：

   ```
   pip install -e ".[dev]"
   ```

   等待安装完成（约 1~3 分钟）。

4. 安装前端依赖：

   ```
   npm --prefix src/frontend install
   ```

   等待安装完成。

### 步骤 6：注册并获取 DeepSeek API Key

本系统使用 DeepSeek V4 Pro 作为大语言模型，需要注册获取 API Key。

1. 打开浏览器，访问 DeepSeek 开放平台：https://platform.deepseek.com/
2. 点击注册账号，使用手机号或邮箱完成注册
3. 登录后，进入 **"API Keys"** 页面
4. 点击 **"创建 API Key"**，为 Key 命名（如 "launchpad"），点击确认
5. **立即复制生成的 Key**（关闭后无法再次查看），保存备用
6. **注意**：API 按使用量计费。新注册用户通常有免费额度。充值方法请参考：https://platform.deepseek.com/api-docs/

### 步骤 7：安装并配置 PostgreSQL

本系统使用 PostgreSQL 存储项目数据。

**7.1 安装 PostgreSQL**

1. 打开浏览器，访问：https://www.postgresql.org/download/windows/
2. 点击 **"Download the installer"**
3. 选择最新版本，下载安装包
4. 双击安装包，一路点击 "Next"
5. 在设置密码页面，**设置一个您能记住的密码**（例如 `admin123`），**建议记录下来**
6. 端口保持默认的 `5432`，完成安装

**7.2 创建数据库**

1. 打开开始菜单，找到 **"pgAdmin 4"** 并启动
2. 首次登录需要设置 pgAdmin 的主密码（可以和之前设置的相同）
3. 在左侧面板中，右键点击 **"Databases"** → **"Create"** → **"Database..."**
4. 在 "Database" 字段输入 `launchpad`，点击 "Save"

### 步骤 8：安装 Docker 并启动 Qdrant

Qdrant 是向量数据库，用于检索历史项目。我们通过 Docker 来运行它。

**8.1 安装 Docker Desktop**

1. 打开浏览器，访问：https://www.docker.com/products/docker-desktop/
2. 点击 **"Download for Windows"**
3. 双击下载的安装包，按照提示完成安装
4. **安装后可能需要重启电脑**

**8.2 启动 Qdrant**

1. 重启后，打开命令提示符（`Win + R`，输入 `cmd`，回车）
2. 输入以下命令并回车：

   ```
   docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

3. 第一次运行会自动下载 Qdrant 镜像（约 2~5 分钟）
4. 验证是否启动成功：打开浏览器，访问 http://localhost:6333/health
   - 如果看到类似 `{"title":"qdrant - vector search engine","version":"..."}` 的页面，说明成功

> **如果 Docker 安装遇到困难**（部分 Windows 版本有兼容性问题），可以使用 Qdrant Cloud 免费版：
> 1. 访问 https://cloud.qdrant.io/ 注册
> 2. 创建免费集群，获取连接 URL
> 3. 在后面的配置中将 `QDRANT_URL` 改为该 URL 即可

### 步骤 9：配置文件

1. 在项目文件夹 `launchpad` 中，找到文件 `.env.example`
2. **复制**这个文件，将副本命名为 `.env`（注意：没有扩展名，就是 `.env`）
   - 可以在文件夹中右键 `.env.example` → 复制 → 粘贴 → 重命名为 `.env`
3. 用记事本打开 `.env` 文件，修改以下内容：

   ```
   DEEPSEEK_API_KEY=您在第6步获取的Key粘贴在这里
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   QDRANT_URL=http://localhost:6333
   DATABASE_URL=postgresql://postgres:您的数据库密码@localhost:5432/launchpad
   MAX_DIALOG_TURNS=3
   CONFIDENCE_THRESHOLD=0.7
   ENABLE_REASONING_STREAM=true
   LLM_MODEL=deepseek-v4-pro
   LLM_TIMEOUT=30
   PARALLEL_AGENT_TIMEOUT=60
   ```

4. 其中：
   - `DEEPSEEK_API_KEY=` 后面粘贴您的 DeepSeek API Key
   - `DATABASE_URL` 中的 `您的数据库密码` 替换为步骤 7.1 中设置的 PostgreSQL 密码

### 步骤 10：初始化数据库

1. 打开命令提示符（`Win + R`，输入 `cmd`，回车）
2. 进入项目目录：

   ```
   cd Desktop\launchpad
   ```

3. 执行数据库迁移：

   ```
   alembic upgrade head
   ```

   如果看到类似 "INFO  [alembic.runtime.migration] Running upgrade ..." 的输出，说明成功。

### 步骤 11：导入历史项目数据

1. 确保 Docker 中的 Qdrant 正在运行（步骤 8.2）
2. 在命令提示符中，进入项目目录后执行：

   ```
   python scripts/seed_qdrant.py
   ```

3. 看到 "Seeded 25 historical projects into Qdrant." 表示成功

### 步骤 12：启动系统

1. 打开命令提示符，进入项目目录：

   ```
   cd Desktop\launchpad
   ```

2. 启动系统（同时启动后端和前端）：

   ```
   make dev
   ```

   如果 `make` 命令不可用，可以分别启动：
   - 后端（先在新命令行窗口中执行）：
     ```
     uvicorn src.api.routes:app --reload --port 8000
     ```
   - 前端（在另一个命令行窗口中执行）：
     ```
     npm --prefix src/frontend run dev
     ```

3. 等待启动完成，看到类似以下提示说明成功：
   - 后端：`Uvicorn running on http://127.0.0.1:8000`
   - 前端：`Local: http://localhost:3000/`

### 步骤 13：开始使用

1. 打开浏览器，访问 **http://localhost:3000**
2. 您将看到 LaunchPad 的主界面
3. 在左侧导航点击 **"新建项目"**
4. 在输入框中用自然语言描述您的项目需求，例如：
   > 我们需要做一个内部考勤管理系统，支持员工打卡、请假申请、加班审批和考勤报表导出。预计有 500 名员工使用。
5. 系统会通过多轮对话向您提问，帮助澄清需求细节
6. 对话完成后，系统自动进行可行性、资源、风险评估
7. **右侧面板**会实时显示推理过程
8. 如果系统提示需要人工审核，检查分析结果后点击 **"人工确认审核"**
9. 审核通过后，系统自动生成立项文档（.docx 格式），保存在项目的 `output/` 目录中

### 常见问题

**Q: 启动时提示 "ModuleNotFoundError"？**
A: 表示依赖未安装完整。重新执行步骤 5：`pip install -e ".[dev]"`

**Q: 页面打不开，提示 "无法连接"？**
A: 确保前端和后端两个命令行窗口都在运行。如果 `make dev` 方式启动，窗口关闭即停止。

**Q: 对话时提示 API 错误？**
A: 检查 `.env` 文件中 `DEEPSEEK_API_KEY` 是否正确填写，以及 DeepSeek 账户是否有余额。

**Q: PostgreSQL 连接失败？**
A: 检查 PostgreSQL 服务是否运行（开始菜单搜索 "Services"，找到 `postgresql` 服务是否已启动），以及 `.env` 中的密码是否正确。

**Q: Qdrant 连接失败？**
A: 检查 Docker 是否运行，Qdrant 容器是否启动（命令提示符输入 `docker ps`，应能看到 `qdrant/qdrant`）。如 Docker 无法安装，改用步骤 8.2 中提到的 Qdrant Cloud。

---

**免责声明**：本系统输出的立项文档由 AI 辅助生成，仅供参考，最终决策需由项目评审委员会确认。
