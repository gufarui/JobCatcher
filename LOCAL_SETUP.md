# JobCatcher 本地开发环境设置指南

## 🚀 快速开始

### 1. 复制环境变量模板
```bash
cp .env-template .env
```

### 2. 关键配置修改

在.env文件中修改以下配置：

#### 🔑 JWT认证配置 (重要！)
```bash
# 本地开发使用固定的SECRET_KEY
SECRET_KEY=dev_jwt_secret_key_for_local_development_only_do_not_use_in_production
```

#### 🗄️ 数据库配置
```bash
# 本地开发使用SQLite，无需安装PostgreSQL
DATABASE_URL=sqlite+aiosqlite:///./jobcatcher_dev.db
```

#### 🌍 应用环境
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
APP_DOMAIN=localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. 可选配置（如果有真实密钥）

如果你有以下服务的API密钥，可以替换：
```bash
# Claude 4 API (如果有真实密钥)
ANTHROPIC_API_KEY=你的真实密钥

# Google OAuth (如果需要测试登录)
GOOGLE_CLIENT_ID=你的客户端ID
GOOGLE_CLIENT_SECRET=你的客户端密钥
```

## 🔧 本地调试重点

### JWT认证调试
- **使用**: `SECRET_KEY` 
- **忽略**: `SESSION_SECRET` (代码中未使用)

### 数据库调试
- 本地使用SQLite: `jobcatcher_dev.db`
- 无需配置PostgreSQL

### API密钥调试
- 大部分功能可以用demo密钥测试
- 只有实际调用外部API时才需要真实密钥

## 📝 完整的本地.env示例

```bash
# LLM配置
ANTHROPIC_API_KEY=sk-demo  # 或你的真实密钥
ANTHROPIC_BASE_URL=https://claude.cloudapi.vip
CLAUDE_TEMPERATURE=0.3

# 认证配置 (关键！)
SECRET_KEY=dev_jwt_secret_key_for_local_development_only
SESSION_SECRET=_M8CG7ZVBLyTf1-c2vWY6v4qwKzcJRcbM0szxiwrwvU

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./jobcatcher_dev.db

# 应用配置
ENVIRONMENT=development
LOG_LEVEL=DEBUG
APP_DOMAIN=localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 其他服务密钥 (可选)
APIFY_TOKEN=demo_token
SERPAPI_KEY=demo_key
PDFMONKEY_KEY=demo_key
```

## 🚀 启动应用

```bash
# 后端
cd backend
uvicorn app.main:app --reload --port 8000

# 前端 
cd frontend
npm run dev
```

## 🔍 调试验证

### 1. 检查JWT认证
```bash
curl http://localhost:8000/auth/me
```

### 2. 检查数据库连接
```bash
# SQLite文件应该会自动创建在项目根目录
ls jobcatcher_dev.db
```

### 3. 检查前端连接
访问: http://localhost:5173

## ⚠️ 重要提醒

1. **SECRET_KEY** 是JWT签名的关键，必须配置
2. **SESSION_SECRET** 当前代码中未使用，可以忽略  
3. **.env文件** 绝不要提交到Git仓库
4. **数据库** 本地开发用SQLite即可
5. **API密钥** 开发阶段用demo值就够了 