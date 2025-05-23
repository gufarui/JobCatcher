# JobCatcher Azure 部署配置指南

## 🚀 Azure App Service 部署步骤

### ⚠️ 重要：.env文件处理
- **绝不将.env文件上传到Azure**
- **所有环境变量通过Azure Application Settings配置**
- **确保.env在.gitignore中被忽略**

### 1. 环境变量配置 (Azure Application Settings)

在Azure Portal中配置以下环境变量：

#### 🔐 认证相关 (Security Critical)
```bash
# 🚨 生产环境必须重新生成！JWT签名的关键密钥
SECRET_KEY=<生成新的64字符随机字符串>

# Google OAuth生产环境凭据
GOOGLE_CLIENT_ID=<生产环境客户端ID>
GOOGLE_CLIENT_SECRET=<生产环境的Google OAuth密钥>

# 注意：SESSION_SECRET当前代码中未使用，可以省略或保持默认值
# SESSION_SECRET=<任意值，当前无影响>
```

生成生产环境SECRET_KEY：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### 🗄️ 数据库配置
```bash
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

#### ☁️ Azure服务
```bash
AZURE_SEARCH_ENDPOINT=https://your-prod-search.search.windows.net
AZURE_SEARCH_KEY=<生产环境搜索密钥>
AZURE_STORAGE_CONNECTION_STRING=<生产环境存储连接字符串>
```

#### 🤖 API服务
```bash
ANTHROPIC_API_KEY=<生产环境Claude密钥>
APIFY_TOKEN=<生产环境Apify令牌>
SERPAPI_KEY=<生产环境SerpAPI密钥>
PDFMONKEY_KEY=<生产环境PDFMonkey密钥>
```

#### 🌍 应用环境配置
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
APP_DOMAIN=your-domain.azurewebsites.net
CORS_ORIGINS=https://your-frontend-domain.com
```

### 2. Azure Portal配置步骤

#### 方法1: Azure Portal GUI (推荐)
```
1. 登录Azure Portal (portal.azure.com)
2. 导航到你的App Service
3. 左侧菜单 → Configuration
4. Application settings 标签
5. 点击 "+ New application setting"
6. 逐个添加上述环境变量
7. 点击 "Save" 保存配置
```

#### 方法2: Azure CLI批量配置
```bash
# 一次性配置多个环境变量
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name jobcatcher-prod \
  --settings \
    SECRET_KEY="生产环境JWT密钥" \
    ANTHROPIC_API_KEY="sk-生产环境密钥" \
    DATABASE_URL="postgresql://用户:密码@主机:端口/数据库" \
    ENVIRONMENT="production" \
    LOG_LEVEL="WARNING"
```

### 3. 创建App Service
```bash
# 创建资源组
az group create --name jobcatcher-rg --location "East US"

# 创建App Service计划
az appservice plan create \
  --name jobcatcher-plan \
  --resource-group jobcatcher-rg \
  --sku B1 \
  --is-linux

# 创建Web App
az webapp create \
  --resource-group jobcatcher-rg \
  --plan jobcatcher-plan \
  --name jobcatcher-prod \
  --runtime "PYTHON|3.9"
```

### 4. 安全配置检查清单

- [ ] **SECRET_KEY**: 重新生成，至少64字符 (🚨 关键！)
- [ ] **GOOGLE_CLIENT_SECRET**: 使用生产环境凭据
- [ ] **DATABASE_URL**: 生产数据库连接
- [ ] **AZURE_SEARCH_KEY**: 生产搜索服务密钥
- [ ] **ENVIRONMENT**: 设置为 "production"
- [ ] **CORS_ORIGINS**: 设置为生产域名
- [ ] **LOG_LEVEL**: 设置为 "WARNING" 或 "ERROR"
- [ ] **确认.env文件未上传**: 检查.gitignore

### 5. 环境差异说明

| 配置项 | 开发环境 | 生产环境 |
|--------|----------|----------|
| **SECRET_KEY** | 固定值，团队共享 | 唯一值，定期轮换 |
| **SESSION_SECRET** | 任意值 (代码未使用) | 任意值 (代码未使用) |
| **DATABASE_URL** | SQLite本地文件 | Azure PostgreSQL |
| **LOG_LEVEL** | DEBUG | WARNING |
| **ENVIRONMENT** | development | production |
| **CORS_ORIGINS** | localhost:3000,5173 | 实际域名 |
| **配置方式** | .env文件 | Azure Application Settings |

### 6. 部署后验证

```bash
# 检查应用是否正常启动
curl https://jobcatcher-prod.azurewebsites.net/health

# 检查环境变量是否正确加载
curl https://jobcatcher-prod.azurewebsites.net/api/config/environment

# 检查认证是否正常 (应返回401，表示认证系统工作)
curl https://jobcatcher-prod.azurewebsites.net/auth/me
```

## 🔄 环境变量管理最佳实践

### 开发环境
- 使用 `.env` 文件
- 可以团队共享（除了个人API密钥）
- 定期从模板更新
- SECRET_KEY可以使用固定值

### 生产环境  
- **绝不使用 .env 文件**
- 使用 Azure App Service Application Settings
- 密钥绝不提交到代码库
- 启用 Azure Key Vault 集成（可选）
- 定期轮换敏感密钥
- SECRET_KEY必须重新生成

### 密钥轮换计划
- **SECRET_KEY**: 每6个月 (关键！)
- API密钥: 根据服务商建议
- 数据库密码: 每3个月
- SESSION_SECRET: 当前无需轮换 (代码未使用)

## 🔐 安全检查
1. 确认.env文件在.gitignore中
2. 确认敏感信息未提交到Git历史
3. 生产环境SECRET_KEY与开发环境不同
4. Azure Application Settings正确配置
5. CORS设置限制为生产域名 