# 部署说明

## 启动顺序

1. `docker compose -f deploy/docker-compose.yml up -d`
2. `./deploy/init_db.ps1`（首次或重建库时）
3. `./deploy/start_inference.ps1`
4. `./deploy/start_backend.ps1`
5. `./deploy/start_frontend.ps1`
6. `./deploy/start_nginx.ps1`（埋点采集，可选）
7. `./deploy/start_flink_job.ps1`（实时特征，可选）

## 模型训练

```powershell
python -m algorithm.training.run_daily
```

## 端口

| 服务 | 端口 |
| --- | --- |
| Vue dev | 5173 |
| Spring Boot | 8080 |
| Python 推理 | 9000 |
| Nginx 埋点 | 8088 |
| MySQL | 3306 |
| Redis | 6379 |
| Kafka | 9092 |
| Milvus | 19530 |
