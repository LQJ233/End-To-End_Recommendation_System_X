# API 接口设计文档

## 1. 通用约定

### 1.1 基础地址

| 服务 | 地址 |
| --- | --- |
| 后端业务 API | `http://localhost:8080/api/v1` |
| 在线推理 API | `http://localhost:9000/api/v1` |
| 行为采集 API | `http://localhost:8088/track` |

### 1.2 通用响应

成功响应（HTTP 200）：

```json
{
  "code": 0,
  "message": "success",
  "requestId": "rec_20260526120000001",
  "data": {}
}
```

业务错误响应：**HTTP status 与业务 code 双重指示**，前端 axios 拦截器优先按 HTTP status 处理跳转/清登录态，业务层再读 body.code 显示文案。

| HTTP status | code 区间 | 典型场景 |
| --- | --- | --- |
| 400 | 400xxx | 参数缺失或非法 |
| 401 | 401xxx | 未登录 / token 失效（前端必须自动清 token + 跳登录页） |
| 403 | 403xxx | 已登录但无权限（不跳登录页，业务层提示） |
| 404 | 404xxx | 资源不存在 |
| 409 | 409xxx | 唯一约束冲突（username/phone/email_exists） |
| 423 | 423xxx | 用户被禁用 / 账号锁定 |
| 429 | 429xxx | 限流（登录频次等） |
| 500 | 500xxx | 内部错误、依赖故障 |

### 1.3 通用错误码
| code | message | 说明 |
| --- | --- | --- |
| 0 | success | 成功 |
| 400001 | invalid_parameter | 参数错误 |
| 401001 | unauthorized | 未登录或用户 ID 无效 |
| 404001 | item_not_found | 商品不存在 |
| 429001 | too_many_requests | 请求过于频繁 |
| 500001 | internal_error | 系统内部错误 |
| 500101 | redis_error | Redis 访问失败 |
| 500102 | mysql_error | MySQL 访问失败 |
| 500201 | inference_error | 推理服务失败 |
| 500202 | milvus_error | 向量检索失败 |
| 500301 | kafka_error | 行为日志写入失败 |

## 2. 后端业务 API

### 2.1 获取首页推荐商品

`GET /recommendations/home`

说明：按游标获取当前用户的推荐商品。如果 Redis 中没有候选，后端可以自动触发刷新。?
请求参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| userId | string | 是 | 用户 ID |
| scene | string | 是 | 默认 `home` |
| cursor | int | 是 | 分页游标，默认 0 |
| size | int | 是 | 每页数量，默认 20 |

响应。
```json
{
  "code": 0,
  "message": "success",
  "requestId": "rec_20260526120000001",
  "data": {
    "scene": "home",
    "cursor": 20,
    "hasMore": true,
    "items": [
      {
        "itemId": "10001",
        "title": "潮流运动",
        "itemCategory": "300",
        "price": 399.00,
        "imageUrl": "http://localhost:8080/static/item/10001.jpg",
        "rankScore": 0.9321
      }
    ]
  }
}
```

### 2.2 刷新首页推荐

`POST /recommendations/refresh`

说明：触发在线推理，生成新的候选商品队列。
请求体：

```json
{
  "userId": "u_10001",
  "scene": "home",
  "triggerType": "manual",
  "excludeItemIds": ["10001", "10002"]
}
```

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| userId | string | 是 | 用户 ID |
| scene | string | 是 | 默认 `home` |
| triggerType | string | 是 | `auto`、`manual`、`exhausted`、`cache_miss` |
| excludeItemIds | array | 是 | 前端已展示商品 ID，用于去重 |

响应。
```json
{
  "code": 0,
  "message": "success",
  "requestId": "rec_20260526120000001",
  "data": {
    "modelVersion": "20260526_0000",
    "candidateSize": 500,
    "items": []
  }
}
```

### 2.3 上报曝光确认

`POST /recommendations/exposure`

说明：后端记录当前推荐批次的曝光状态，用于判断是否全部曝光和缓存召回退场。前端行为日志仍发送到 Nginx）
请求体：

```json
{
  "userId": "u_10001",
  "requestId": "rec_20260526120000001",
  "itemIds": ["10001", "10002"],
  "timestamp": 1780000000000
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "allExposed": false
  }
}
```

### 2.4 查询商品详情卡片

`GET /items/batch`

请求参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| itemIds | string | 是 | 逗号分隔商品 ID |

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "itemId": "10001",
        "title": "潮流运动",
        "itemCategory": "300",
        "price": 399.00,
        "imageUrl": "http://localhost:8080/static/item/10001.jpg",
        "status": 1
      }
    ]
  }
}
```

### 2.5 模拟购买

`POST /orders/mock`

说明：本期不做真实订单和支付，仅用于演示购买行为。
请求体：

```json
{
  "userId": "u_10001",
  "itemId": "10001",
  "requestId": "rec_20260526120000001"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "orderId": "mock_order_20260526120000001"
  }
}
```

## 3. 行为采集 API

### 3.1 Nginx 行为采集

`POST /track/behavior`

说明：前端只向日志采集服务发送行为数据，Nginx Lua 将数据推到 Kafka。
请求体：

```json
{
  "userId": "u_10001",
  "itemId": "10001",
  "behaviorType": 1,
  "timestamp": 1780000000000,
  "requestId": "rec_20260526120000001",
  "scene": "home"
}
```

响应。
```json
{
  "code": 0,
  "message": "accepted"
}
```

行为类型：

| behaviorType | 含义 |
| --- | --- |
| 0 | 曝光 |
| 1 | 点击 |
| 2 | 收藏 |
| 3 | 加购物车 |
| 4 | 购买 |

## 4. 在线推理 API

### 4.1 健康检查
`GET /inference/health`

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "UP",
    "modelVersion": "20260526_0000",
    "recallLoaded": true,
    "rankingLoaded": true
  }
}
```

### 4.2 在线推荐推理

`POST /inference/recommend`

请求体：

```json
{
  "requestId": "rec_20260526120000001",
  "userId": "u_10001",
  "scene": "home",
  "recallSize": 500,
  "excludeItemIds": ["10001"],
  "recallOptions": {
    "enableVectorRecall": true,
    "enableLbsRecall": true,
    "enableTagRecall": true,
    "lbsMaxDistanceKm": 50,
    "tagDimensions": ["item_category", "brand", "style", "price_bucket"]
  }
}
```

说明

- 后端调用推理服务时只传 `userId`、`requestId`、`scene`、过滤列表和召回开关。

- `clickSeq`、`cartSeq`、`purchaseSeq`、`lastGeoHash`、`tagPreferences` 等实时特征不再由后端读取后塞入请求体

- Python 推理服务统一读 Redis 读取 `feature:user:*`、`rec:lbs:index:*`、`rec:tag:index:*` 等推荐特征和召回索引。
响应。
```json
{
  "code": 0,
  "message": "success",
  "requestId": "rec_20260526120000001",
  "data": {
    "modelVersion": "20260526_0000",
    "featureSnapshotTime": 1780000000000,
    "recallDebug": {
      "vectorRecallSize": 500,
      "lbsRecallSize": 120,
      "tagRecallSize": 230,
      "mergedSize": 610
    },
    "items": [
      {
        "itemId": "10008",
        "recallChannels": ["vector", "tag"],
        "recallScore": 0.82,
        "ctr": 0.31,
        "cvr": 0.04,
        "rankScore": 0.334
      }
    ]
  }
}
```

### 4.3 重载模型

`POST /inference/model/reload`

说明：本地发布新模型后，通知推理服务重新加载模型文件。
请求体：

```json
{
  "modelVersion": "20260527_0000",
  "recallModelPath": "E:/End-To-End_Recommendation_System_X/data/model/recall_user_tower.pt",
  "rankingModelPath": "E:/End-To-End_Recommendation_System_X/data/model/ranking_mmoe.pt",
  "featureConfigPath": "E:/End-To-End_Recommendation_System_X/data/model/feature_config.json"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "loaded": true
  }
}
```

## 5. 分页和刷新约

- 前端首次进入首页调用 `POST /recommendations/refresh`，再调用 `GET /recommendations/home` 获取第一页。

- 前端接近底部 200px 时调。`GET /recommendations/home` 获取下一页。

- 前端维护 `displayedItemIds`，过滤重复商品。

- 前端手动刷新调用 `POST /recommendations/refresh`，并清空本地推荐列表

- 如果后端返回 `hasMore=false`，前端可触发 `triggerType=exhausted` 的刷新。
## 补充：认证与用户管理 API

### A.1 用户注册

`POST /auth/register`

请求体：

```json
{
  "username": "alice",
  "password": "Password123",
  "nickname": "Alice",
  "phone": "13800000000",
  "email": "alice@example.com"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "userId": "u_10001",
    "username": "alice",
    "nickname": "Alice"
  }
}
```

错误码补充：

| code | message | 说明 |
| --- | --- | --- |
| 403001 | forbidden | 无权限访 |
| 409001 | username_exists | 用户名已存在 |
| 409002 | phone_exists | 手机号已存在 |
| 423001 | user_disabled | 用户已被禁用 |
| 423001 | account_locked | 该账号连续 5 次密码错误后锁定 15 min |
| 429001 | too_many_login_attempts | 。IP 。5 min 内累计失。。30  |

### A.2 用户登录

`POST /auth/login`

请求体：

```json
{
  "username": "alice",
  "password": "Password123"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "accessToken": "jwt-token",
    "tokenType": "Bearer",
    "expiresIn": 7200,
    "user": {
      "userId": "u_10001",
      "username": "alice",
      "nickname": "Alice",
      "roles": ["USER"]
    }
  }
}
```

### A.3 当前用户信息

`GET /users/me`

Header。?
```text
Authorization: Bearer <accessToken>
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "userId": "u_10001",
    "username": "alice",
    "nickname": "Alice",
    "avatarUrl": "",
    "phone": "13800000000",
    "email": "alice@example.com",
    "gender": 0,
    "ageLevel": "18_24",
    "defaultGeohash": "wx4g0",
    "roles": ["USER"],
    "status": 1
  }
}
```

### A.4 修改当前用户资料

`PUT /users/me`

请求体：

```json
{
  "nickname": "Alice New",
  "avatarUrl": "http://localhost:8080/static/avatar/u_10001.jpg",
  "phone": "13800000001",
  "email": "alice_new@example.com",
  "gender": 2,
  "ageLevel": "18_24",
  "defaultGeohash": "wx4g0"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.5 修改密码

`PUT /users/me/password`

请求体：

```json
{
  "oldPassword": "Password123",
  "newPassword": "Password456"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.5.5 续签 access token

`POST /auth/refresh`

请求体：

```json
{ "refreshToken": "<base64url>" }
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "accessToken": "jwt-token-here",
    "refreshToken": "<!-- base64url>",
    "tokenType": "Bearer",
    "expiresIn": 7200,
    "refreshExpiresIn": 2592000,
    "user": { "userId": "u_10001", "username": "alice", "nickname": "Alice", "roles": ["USER"] }
  }
}
```

约定

- refresh token 一次性，每次 refresh 都会**旋转**出新的 refreshsh token，前端必须替换本地保存。

- refresh token 默认 30 天，由 `app.auth.refreshTokenExpireDays` 控制

- 用户被禁用或不存。。拒绝 `401 invalid_refresh_token` / `423 user_disabled`。
- 触发 `forceLogoutAll` 时（管理员禁用 / 改密 / 调角色），该用户的所有 refreshsh token 一并 revokee。
### A.6 退出登录
`POST /auth/logout`

说明：MVP 可以只由前端删除 token；如果启用 Redis 黑名单，则后端将 tokenId 写入 `auth:blacklist:{tokenId}`。
响应。
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.7 管理员分页查询用户
`GET /admin/users`

权限：`ADMIN`

请求参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 是 | 用户名、昵称、手机号模糊查询 |
| status | int | 是 | 1 正常、1 禁用 |
| roleCode | string | 是 | `USER` 或 `ADMIN` |
| page | int | 是 | 页码，默认 1 |
| size | int | 是 | 每页数量，默认 20 |

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 1,
    "records": [
      {
        "userId": "u_10001",
        "username": "alice",
        "nickname": "Alice",
        "phone": "13800000000",
        "status": 1,
        "roles": ["USER"],
        "createdAt": "2026-05-26 12:00:00"
      }
    ]
  }
}
```

### A.8 管理员更新用户状态
`PUT /admin/users/{userId}/status`

权限：`ADMIN`

请求体：

```json
{
  "status": 0
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.9 管理员重置密码
`PUT /admin/users/{userId}/password`

权限：`ADMIN`

请求体：

```json
{
  "newPassword": "Password123"
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.10 管理员调整角色
`PUT /admin/users/{userId}/roles`

权限：`ADMIN`

请求体：

```json
{
  "roles": ["USER", "ADMIN"]
}
```

响应。
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.11 与推荐 API 的约

- 登录用户调用推荐接口时，后端优先使用 JWT 中的 `userId`
- 未登录游客可以继续通过请求参数传 `userId`，但只能作为临时游客 ID。
- 管理员接口统一要求 Header 中携带 `Authorization: Bearer <accessToken>`，且 token 中包含 `ADMIN` 角色。
### A.12 登录限流约定

| 触发 | 响应 code | 提示 |
| --- | --- | --- |
| 同一 IP 5 min 内累计失。。30  | `429001` | `too_many_login_attempts` |
| 同一账号连续 5 次密码错误 | `423001` | `account_locked`（锁定 15 min） |
| 登录成功 | 是 | 自动清除该账号的失败计数 |

阈值由 `app.auth.loginRateLimit.*` 控制，详见 `10_高并发设计.md` §5。
### A.13 监控端点

公开（无需鉴权）：

| 路径 | 说明 |
| --- | --- |
| `GET /actuator/health` | 健康检查；包含 `inference` 熔断器状态 |
| `GET /actuator/circuitbreakers` | Resilience4j 熔断器列。+ 当前状态 |
| `GET /actuator/circuitbreakerevents/inference` | 推理熔断器最近事件流 |
| `GET /actuator/metrics/...` | 指标（线程池队列长度、Hikari 连接数、Lettuce 命令延迟等） |
| `GET /actuator/prometheus` | Prometheus scrape 端点（含 trace / Hikari / HTTP / Tomcat 指标） |
| `GET http://localhost:9000/metrics` | Python 推理 Prometheus（含 `recsys_recall_channel_*`、`recsys_rank_latency_ms`、`recsys_fallback_total` 等 |

### A.14 分布式 trace

后端每次推理调用都会注入 W3C `traceparent: 00-{traceId}-{spanId}-01`。
- Java 端：Micrometer Tracing + OTEL；`@Observed("recommendation.refresh")` 自动 span；`RestTemplate` interceptor 自动 headerr。
- Python 端：`TraceContextMiddleware` 解析 `traceparent`，把 `trace_id / span_id / request_id` 注入日志 context。响应头 `x-trace-id` 让前端能采集

- 默认 OTLP 不导出（`otel.exporter.otlp.enabled=false`）。要观测时部。Jaeger / Tempo / Otel-Collector 为 `true`。