# 🚀 TradingAgents-CN 阿里云部署指南

## 📊 数据存储架构

### 当前状态 ✅
- **MongoDB**: 3条历史记录已成功迁移到数据库
- **Redis**: 用于缓存和临时数据
- **文件系统**: 作为备用存储方案

## 🛡️ 阿里云部署方案

### 方案A: 云数据库部署（推荐）⭐

#### 1. 阿里云MongoDB云数据库
```bash
# 优势：
✅ 自动备份和恢复
✅ 高可用和容灾
✅ 自动扩容
✅ 安全防护
✅ 监控告警

# 配置示例：
MONGODB_HOST=dds-xxxxx.mongodb.rds.aliyuncs.com
MONGODB_PORT=3717
MONGODB_USERNAME=root
MONGODB_PASSWORD=your_secure_password
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin
```

#### 2. 阿里云Redis云数据库
```bash
# 配置示例：
REDIS_HOST=r-xxxxx.redis.rds.aliyuncs.com  
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
```

### 方案B: 文件存储部署

#### 1. 阿里云NAS（网络附加存储）
```yaml
# docker-compose.yml
services:
  web:
    volumes:
      - /mnt/nas/tradingagents/data:/app/data
      - /mnt/nas/tradingagents/logs:/app/logs
    environment:
      MONGODB_ENABLED: "false"
      REDIS_ENABLED: "false"
```

#### 2. 阿里云OSS对象存储
```bash
# 环境变量
OSS_BUCKET=tradingagents-data
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_access_key
OSS_ACCESS_KEY_SECRET=your_access_secret
```

## 🔧 部署配置文件

### docker-compose.prod.yml（生产环境）
```yaml
version: '3.8'

services:
  web:
    image: tradingagents-cn:latest
    container_name: tradingagents-web
    ports:
      - "8501:8501"
    environment:
      # 数据库配置（云数据库）
      MONGODB_ENABLED: "true"
      MONGODB_HOST: ${MONGODB_HOST}
      MONGODB_PORT: ${MONGODB_PORT}
      MONGODB_USERNAME: ${MONGODB_USERNAME}
      MONGODB_PASSWORD: ${MONGODB_PASSWORD}
      MONGODB_DATABASE: ${MONGODB_DATABASE}
      
      REDIS_ENABLED: "true"
      REDIS_HOST: ${REDIS_HOST}
      REDIS_PORT: ${REDIS_PORT}
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      
      # 应用配置
      PYTHONUNBUFFERED: 1
      TZ: "Asia/Shanghai"
      TRADINGAGENTS_LOG_LEVEL: "INFO"
      
      # API密钥（使用阿里云密钥管理）
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
      FINNHUB_API_KEY: ${FINNHUB_API_KEY}
      
    volumes:
      # 日志持久化（可选）
      - /var/log/tradingagents:/app/logs
      
    restart: unless-stopped
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### .env.prod（生产环境变量）
```bash
# 阿里云MongoDB配置
MONGODB_HOST=dds-xxxxx.mongodb.rds.aliyuncs.com
MONGODB_PORT=3717
MONGODB_USERNAME=root
MONGODB_PASSWORD=your_secure_mongodb_password
MONGODB_DATABASE=tradingagents

# 阿里云Redis配置  
REDIS_HOST=r-xxxxx.redis.rds.aliyuncs.com
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password

# API密钥
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FINNHUB_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🚀 部署步骤

### 1. 准备阿里云资源
```bash
# 创建MongoDB云数据库实例
# 创建Redis云数据库实例  
# 配置ECS实例或容器服务ACK
# 设置安全组规则
```

### 2. 数据迁移
```bash
# 已完成：本地数据 → MongoDB
# 验证：3条历史记录成功迁移
# 备份：定期导出MongoDB数据
```

### 3. 部署应用
```bash
# 构建镜像
docker build -t tradingagents-cn:latest .

# 推送到阿里云镜像仓库
docker tag tradingagents-cn:latest registry.cn-hangzhou.aliyuncs.com/your_namespace/tradingagents-cn:latest
docker push registry.cn-hangzhou.aliyuncs.com/your_namespace/tradingagents-cn:latest

# 部署到生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## 🔐 安全配置

### 1. 网络安全
```bash
# 配置VPC专有网络
# 设置安全组规则（仅开放必要端口）
# 使用内网连接数据库
```

### 2. 密钥管理
```bash
# 使用阿里云密钥管理服务KMS
# 环境变量加密存储
# 定期轮换密钥
```

## 📊 监控和运维

### 1. 应用监控
```bash
# 使用阿里云应用实时监控ARMS
# 配置日志收集和分析
# 设置告警规则
```

### 2. 数据库监控
```bash
# MongoDB云监控
# Redis性能指标
# 自动备份策略
```

## 🔄 备份和恢复

### 1. 数据备份
```bash
# MongoDB自动备份（每日）
# 历史记录文件备份到OSS
# 配置文件版本控制
```

### 2. 灾难恢复
```bash
# 跨可用区部署
# 数据库读写分离
# 应用多实例部署
```

## 💡 部署建议

### 优先级排序：
1. **🥇 推荐**: 阿里云MongoDB + Redis云数据库
2. **🥈 备选**: 文件存储 + NAS持久化
3. **🥉 开发**: 本地Docker部署

### 成本优化：
- 使用按量付费测试环境
- 生产环境选择包年包月
- 配置自动扩缩容策略

### 性能优化：
- 选择合适的实例规格
- 配置CDN加速静态资源
- 数据库连接池优化

---

📞 **技术支持**: 如需部署协助，请联系技术团队
🔗 **相关文档**: [阿里云MongoDB文档](https://help.aliyun.com/product/26340.html)
