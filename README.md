# JobCatcher - 智能求职辅助平台

一个基于FastAPI + Vue3 + LangGraph + Claude 4的低成本求职辅助平台，提供智能职位搜索、AI简历分析与优化、技能热点图可视化等功能。

## 🚀 核心功能

- **多源职位聚合**：集成StepStone、Google Jobs、JobsPikr、CoreSignal等多个职位数据源
- **AI简历分析**：基于Claude 4的简历解析、匹配度评分和改写建议
- **智能对话助手**：支持职业咨询、岗位推荐等聊天式交互
- **技能热点图**：可视化展示行业技能需求趋势
- **一键简历生成**：自动生成优化后的PDF简历
- **Google OAuth登录**：便捷的用户认证系统

## 🛠 技术栈

### 后端
- **FastAPI** - 现代、高性能的Python Web框架
- **LangChain/LangGraph** - LLM应用开发框架，支持多Agent架构
- **Claude 4** - Anthropic的先进语言模型
- **Azure AI Search** - 向量化搜索与RAG检索
- **PostgreSQL** - 关系型数据库
- **Azure Blob Storage** - 文件存储服务

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Vite** - 极速的前端构建工具
- **Pinia** - Vue的状态管理库
- **Element Plus** - Vue 3组件库
- **Chart.js** - 图表可视化库

### 部署
- **Azure App Service** - 单容器云部署
- **Docker** - 容器化部署
- **GitHub Actions** - CI/CD自动化

## 📋 环境要求

- Python 3.11+
- Node.js 18+
- Docker (可选)

## ⚙️ 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/your-username/JobCatcher.git
cd JobCatcher
```

### 2. 环境变量配置
复制环境变量模板并填入相应的API密钥：
```bash
cp .env.example .env
```

### 3. 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. 前端启动
```bash
cd frontend
npm install
npm run dev
```

### 5. 使用Docker (可选)
```bash
docker-compose up --build
```

## 🔑 API密钥申请

项目集成了多个第三方服务，需要申请以下API密钥：

| 服务 | 用途 | 免费额度 | 申请链接 |
|------|------|----------|----------|
| Anthropic Claude 4 | LLM核心 | $5试用 | [anthropic.com](https://www.anthropic.com/api) |
| Apify StepStone | 职位抓取 | $5平台信用 | [apify.com](https://apify.com/) |
| SerpAPI | Google Jobs | 100 req/月 | [serpapi.com](https://serpapi.com/) |
| APILayer | 简历解析 | 100 req/月 | [apilayer.com](https://apilayer.com/) |
| PDFMonkey | PDF生成 | 20 PDF/月 | [pdfmonkey.io](https://pdfmonkey.io/) |
| Azure AI Search | 向量搜索 | 3索引/50MB | [Azure Portal](https://portal.azure.com/) |
| Google OAuth 2.0 | 用户认证 | 100用户 | [Google Cloud Console](https://console.cloud.google.com/) |

## 📁 项目结构

```
JobCatcher/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── agents/         # LangGraph多Agent模块
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── main.py         # 应用入口
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile         # 后端容器配置
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── views/          # 页面视图
│   │   ├── stores/         # Pinia状态管理
│   │   └── api/            # API接口
│   ├── package.json        # Node.js依赖
│   └── vite.config.ts      # Vite配置
├── docker-compose.yml      # Docker编排
├── .env.example           # 环境变量模板
└── README.md              # 项目说明
```

## 🤝 贡献指南

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱：your-email@example.com
- GitHub Issues：[提交问题](https://github.com/your-username/JobCatcher/issues)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！ 