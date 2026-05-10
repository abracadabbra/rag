# RAG 系统基础设施部署指南

## 概述

本指南说明如何使用 Docker Compose 部署 RAG 系统的基础设施，包括：
- **Milvus**：向量数据库（用于存储和检索文档向量）
- **Redis**：会话状态存储（用于多轮对话）
- **MinIO**：对象存储（Milvus 依赖）
- **etcd**：元数据存储（Milvus 依赖）

## 前置要求

### 系统要求

- **操作系统**：Linux / macOS / Windows (with WSL2)
- **CPU**：至少 4 核
- **内存**：至少 8GB（推荐 16GB）
- **磁盘**：至少 50GB 可用空间

### 软件要求

- **Docker**：20.10+
- **Docker Compose**：2.0+

### 安装 Docker（如果未安装）

**macOS:**
```bash
brew install --cask docker
```

**Linux (Ubuntu):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**验证安装:**
```bash
docker --version
docker-compose --version
```

## 快速开始

### 1. 启动所有服务

```bash
cd infrastructure
docker-compose up -d
```

### 2. 检查服务状态

```bash
docker-compose ps
```

预期输出：
```
NAME                COMMAND                  SERVICE             STATUS              PORTS
milvus-etcd         "etcd -advertise-cli…"   etcd                running             2379-2380/tcp
milvus-minio        "/usr/bin/docker-ent…"   minio               running             0.0.0.0:9000-9001->9000-9001/tcp
milvus-standalone   "/tini -- milvus run…"   milvus              running (healthy)   0.0.0.0:9091->9091/tcp, 0.0.0.0:19530->19530/tcp
rag-redis           "docker-entrypoint.s…"   redis               running (healthy)   0.0.0.0:6379->6379/tcp
redis-commander     "docker-entrypoint.s…"   redis-commander     running             0.0.0.0:8081->8081/tcp
```

### 3. 验证服务健康

**Milvus:**
```bash
curl http://localhost:9091/healthz
# 预期输出: OK
```

**Redis:**
```bash
docker exec rag-redis redis-cli ping
# 预期输出: PONG
```

### 4. 创建 Milvus Collection

```bash
# 安装 Python 依赖
pip install pymilvus

# 创建 Collection
python infrastructure/milvus_schema.py --action create
```

预期输出：
```
创建 Collection: unified_docs
创建向量索引...
创建标量索引...
✅ Collection unified_docs 创建成功！
   - 向量维度: 1024
   - 索引类型: IVF_FLAT
   - 支持场景: risk_rule, model_card, simulation, profit
```

## 服务访问

| 服务 | 地址 | 用途 |
|------|------|------|
| Milvus | `localhost:19530` | 向量数据库 gRPC 接口 |
| Milvus Web UI | `localhost:9091` | Milvus 健康检查 |
| MinIO Console | `http://localhost:9001` | 对象存储管理界面 |
| Redis | `localhost:6379` | Redis 数据库 |
| Redis Commander | `http://localhost:8081` | Redis 可视化管理 |

### MinIO 登录

- **地址**: http://localhost:9001
- **用户名**: `minioadmin`
- **密码**: `minioadmin`

### Redis Commander 登录

- **地址**: http://localhost:8081
- 无需登录，直接访问

## 常用命令

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 启动指定服务
docker-compose up -d milvus redis
```

### 停止服务

```bash
# 停止所有服务
docker-compose stop

# 停止指定服务
docker-compose stop milvus
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启指定服务
docker-compose restart milvus
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看指定服务日志
docker-compose logs -f milvus
docker-compose logs -f redis
```

### 清理数据

```bash
# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除容器和数据卷（⚠️ 会删除所有数据）
docker-compose down -v
```

## Milvus Collection 管理

### 查看 Collection 信息

```bash
python infrastructure/milvus_schema.py --action info
```

### 删除 Collection

```bash
python infrastructure/milvus_schema.py --action drop --collection unified_docs
```

### 重新创建 Collection

```bash
python infrastructure/milvus_schema.py --action create --drop-old
```

## 数据持久化

所有数据存储在 Docker 卷中，即使容器删除，数据也会保留。

### 查看数据卷

```bash
docker volume ls | grep rag
```

输出：
```
local     infrastructure_etcd_data
local     infrastructure_milvus_data
local     infrastructure_minio_data
local     infrastructure_redis_data
```

### 备份数据

```bash
# 备份 Redis
docker exec rag-redis redis-cli SAVE
docker cp rag-redis:/data/dump.rdb ./backup/redis_backup_$(date +%Y%m%d).rdb

# 备份 Milvus（通过 MinIO）
# 访问 http://localhost:9001 下载 bucket 数据
```

## 性能调优

### Milvus 索引优化

**开发环境（数据量 < 10万）：**
```python
index_params = {
    "metric_type": "IP",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}
```

**生产环境（数据量 > 10万）：**
```python
index_params = {
    "metric_type": "IP",
    "index_type": "HNSW",
    "params": {
        "M": 16,
        "efConstruction": 200
    }
}
```

### Redis 内存优化

编辑 `docker-compose.yml`，添加内存限制：
```yaml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

## 故障排查

### Milvus 启动失败

**问题**: `milvus-standalone` 容器一直重启

**解决方案**:
1. 检查日志：`docker-compose logs milvus`
2. 确保 etcd 和 minio 已启动：`docker-compose ps`
3. 增加启动等待时间（修改 `healthcheck.start_period`）

### Redis 连接失败

**问题**: `Connection refused` 错误

**解决方案**:
1. 检查 Redis 是否运行：`docker-compose ps redis`
2. 检查端口占用：`lsof -i :6379`
3. 重启 Redis：`docker-compose restart redis`

### 磁盘空间不足

**问题**: 容器启动失败，提示磁盘空间不足

**解决方案**:
1. 清理 Docker 缓存：`docker system prune -a`
2. 删除旧的数据卷：`docker volume prune`
3. 检查磁盘空间：`df -h`

## 监控与维护

### 资源使用监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 定期维护

**每周：**
- 检查日志大小：`docker-compose logs --tail=100`
- 检查磁盘空间：`df -h`

**每月：**
- 备份数据（Redis + Milvus）
- 清理旧日志：`docker-compose logs --tail=0`

## 生产环境部署建议

### 1. 使用外部存储

将数据卷挂载到外部存储（NFS、EBS）：
```yaml
volumes:
  milvus_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server,rw
      device: ":/path/to/milvus"
```

### 2. 配置资源限制

```yaml
milvus:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G
```

### 3. 启用 TLS

为 Milvus 和 Redis 配置 TLS 加密连接。

### 4. 配置监控

集成 Prometheus + Grafana 监控 Milvus 和 Redis。

## 下一步

基础设施部署完成后，可以开始：
1. 开发数据摄入脚本（`ingestion/ingest.py`）
2. 搭建 FastAPI 服务（`api/main.py`）
3. 导入第一批数据

参考：
- [数据准备指南](../数据准备指南.md)
- [阶段0 PRD](.trellis/tasks/05-07-phase0-infrastructure/prd.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-05-07
