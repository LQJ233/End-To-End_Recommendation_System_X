# API 鎺ュ彛璁捐鏂囨。

## 1. 閫氱敤绾﹀畾

### 1.1 鍩虹鍦板潃

| 鏈嶅姟 | 鍦板潃 |
| --- | --- |
| 鍚庣涓氬姟 API | `http://localhost:8080/api/v1` |
| 鍦ㄧ嚎鎺ㄧ悊 API | `http://localhost:9000/api/v1` |
| 琛屼负閲囬泦 API | `http://localhost:8088/track` |

### 1.2 閫氱敤鍝嶅簲

鎴愬姛鍝嶅簲锛圚TTP 200锛夛細

```json
{
  "code": 0,
  "message": "success",
  "requestId": "rec_20260526120000001",
  "data": {}
}
```

涓氬姟閿欒鍝嶅簲锛?*HTTP status 涓庝笟鍔?code 鍙岄噸鎸囩ず**锛屽墠绔?axios 鎷︽埅鍣ㄤ紭鍏堟寜 HTTP status 澶勭悊璺宠浆/娓呯櫥褰曟€侊紝涓氬姟灞傚啀鎸?body.code 鏄剧ず鏂囨銆?
| HTTP status | code 鍖洪棿 | 鍏稿瀷鍦烘櫙 |
| --- | --- | --- |
| 400 | 400xxx | 鍙傛暟缂哄け鎴栭潪娉?|
| 401 | 401xxx | 鏈櫥褰?/ token 澶辨晥锛堝墠绔繀椤昏嚜鍔ㄦ竻 token + 璺崇櫥褰曢〉锛?|
| 403 | 403xxx | 宸茬櫥褰曚絾鏃犳潈闄愶紙涓嶈烦鐧诲綍椤碉紝涓氬姟灞傛彁绀猴級 |
| 404 | 404xxx | 璧勬簮涓嶅瓨鍦?|
| 409 | 409xxx | 鍞竴绾︽潫鍐茬獊锛坲sername/phone/email_exists锛?|
| 423 | 423xxx | 鐢ㄦ埛琚鐢?/ 璐﹀彿閿佸畾 |
| 429 | 429xxx | 闄愭祦锛堢櫥褰曢娆＄瓑锛?|
| 500 | 500xxx | 鍐呴儴閿欒銆佷緷璧栨晠闅?|

### 1.3 閫氱敤閿欒鐮?
| code | message | 璇存槑 |
| --- | --- | --- |
| 0 | success | 鎴愬姛 |
| 400001 | invalid_parameter | 鍙傛暟閿欒 |
| 401001 | unauthorized | 鏈櫥褰曟垨鐢ㄦ埛 ID 鏃犳晥 |
| 404001 | item_not_found | 鍟嗗搧涓嶅瓨鍦?|
| 429001 | too_many_requests | 璇锋眰杩囦簬棰戠箒 |
| 500001 | internal_error | 绯荤粺鍐呴儴閿欒 |
| 500101 | redis_error | Redis 璁块棶澶辫触 |
| 500102 | mysql_error | MySQL 璁块棶澶辫触 |
| 500201 | inference_error | 鎺ㄧ悊鏈嶅姟澶辫触 |
| 500202 | milvus_error | 鍚戦噺妫€绱㈠け璐?|
| 500301 | kafka_error | 琛屼负鏃ュ織鍐欏叆澶辫触 |

## 2. 鍚庣涓氬姟 API

### 2.1 鑾峰彇棣栭〉鎺ㄨ崘鍟嗗搧

`GET /recommendations/home`

璇存槑锛氭寜娓告爣鑾峰彇褰撳墠鐢ㄦ埛鐨勬帹鑽愬晢鍝併€傚鏋?Redis 涓病鏈夊€欓€夛紝鍚庣鍙互鑷姩瑙﹀彂鍒锋柊銆?
璇锋眰鍙傛暟锛?
| 鍙傛暟 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
| --- | --- | --- | --- |
| userId | string | 鏄?| 鐢ㄦ埛 ID |
| scene | string | 鍚?| 榛樿 `home` |
| cursor | int | 鍚?| 鍒嗛〉娓告爣锛岄粯璁?0 |
| size | int | 鍚?| 姣忛〉鏁伴噺锛岄粯璁?20 |

鍝嶅簲锛?
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
        "title": "娼祦杩愬姩闉?,
        "itemCategory": "300",
        "price": 399.00,
        "imageUrl": "http://localhost:8080/static/item/10001.jpg",
        "rankScore": 0.9321
      }
    ]
  }
}
```

### 2.2 鍒锋柊棣栭〉鎺ㄨ崘

`POST /recommendations/refresh`

璇存槑锛氳Е鍙戝湪绾挎帹鐞嗭紝鐢熸垚鏂扮殑鍊欓€夊晢鍝侀槦鍒椼€?
璇锋眰浣擄細

```json
{
  "userId": "u_10001",
  "scene": "home",
  "triggerType": "manual",
  "excludeItemIds": ["10001", "10002"]
}
```

鍙傛暟锛?
| 鍙傛暟 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
| --- | --- | --- | --- |
| userId | string | 鏄?| 鐢ㄦ埛 ID |
| scene | string | 鍚?| 榛樿 `home` |
| triggerType | string | 鏄?| `auto`銆乣manual`銆乣exhausted`銆乣cache_miss` |
| excludeItemIds | array | 鍚?| 鍓嶇宸插睍绀哄晢鍝?ID锛岀敤浜庡幓閲?|

鍝嶅簲锛?
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

### 2.3 涓婃姤鏇濆厜纭

`POST /recommendations/exposure`

璇存槑锛氬悗绔褰曞綋鍓嶆帹鑽愭壒娆＄殑鏇濆厜鐘舵€侊紝鐢ㄤ簬鍒ゆ柇鏄惁鍏ㄩ儴鏇濆厜鍜岀紦瀛樺彫鍥為€€鍦恒€傚墠绔涓烘棩蹇椾粛鍙戦€佸埌 Nginx銆?
璇锋眰浣擄細

```json
{
  "userId": "u_10001",
  "requestId": "rec_20260526120000001",
  "itemIds": ["10001", "10002"],
  "timestamp": 1780000000000
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "allExposed": false
  }
}
```

### 2.4 鏌ヨ鍟嗗搧璇︽儏鍗＄墖

`GET /items/batch`

璇锋眰鍙傛暟锛?
| 鍙傛暟 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
| --- | --- | --- | --- |
| itemIds | string | 鏄?| 閫楀彿鍒嗛殧鍟嗗搧 ID |

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "itemId": "10001",
        "title": "娼祦杩愬姩闉?,
        "itemCategory": "300",
        "price": 399.00,
        "imageUrl": "http://localhost:8080/static/item/10001.jpg",
        "status": 1
      }
    ]
  }
}
```

### 2.5 妯℃嫙璐拱

`POST /orders/mock`

璇存槑锛氭湰鏈熶笉鍋氱湡瀹炶鍗曞拰鏀粯锛屼粎鐢ㄤ簬婕旂ず璐拱琛屼负銆?
璇锋眰浣擄細

```json
{
  "userId": "u_10001",
  "itemId": "10001",
  "requestId": "rec_20260526120000001"
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "orderId": "mock_order_20260526120000001"
  }
}
```

## 3. 琛屼负閲囬泦 API

### 3.1 Nginx 琛屼负閲囬泦

`POST /track/behavior`

璇存槑锛氬墠绔彧鍚戞棩蹇楅噰闆嗘湇鍔″彂閫佽涓烘暟鎹紝Nginx Lua 灏嗘暟鎹帹鍏?Kafka銆?
璇锋眰浣擄細

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

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "accepted"
}
```

琛屼负绫诲瀷锛?
| behaviorType | 鍚箟 |
| --- | --- |
| 0 | 鏇濆厜 |
| 1 | 鐐瑰嚮 |
| 2 | 鏀惰棌 |
| 3 | 鍔犺喘鐗╄溅 |
| 4 | 璐拱 |

## 4. 鍦ㄧ嚎鎺ㄧ悊 API

### 4.1 鍋ュ悍妫€鏌?
`GET /inference/health`

鍝嶅簲锛?
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

### 4.2 鍦ㄧ嚎鎺ㄨ崘鎺ㄧ悊

`POST /inference/recommend`

璇锋眰浣擄細

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

璇存槑锛?
- 鍚庣璋冪敤鎺ㄧ悊鏈嶅姟鏃跺彧浼?`userId`銆乣requestId`銆乣scene`銆佽繃婊ゅ垪琛ㄥ拰鍙洖寮€鍏炽€?- `clickSeq`銆乣cartSeq`銆乣purchaseSeq`銆乣lastGeoHash`銆乣tagPreferences` 绛夊疄鏃剁壒寰佷笉鍐嶇敱鍚庣璇诲彇鍚庡鍏ヨ姹備綋銆?- Python 鎺ㄧ悊鏈嶅姟缁熶竴浠?Redis 璇诲彇 `feature:user:*`銆乣rec:lbs:index:*`銆乣rec:tag:index:*` 绛夋帹鑽愮壒寰佸拰鍙洖绱㈠紩銆?
鍝嶅簲锛?
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

### 4.3 閲嶈浇妯″瀷

`POST /inference/model/reload`

璇存槑锛氭湰鍦板彂甯冩柊妯″瀷鍚庯紝閫氱煡鎺ㄧ悊鏈嶅姟閲嶆柊鍔犺浇妯″瀷鏂囦欢銆?
璇锋眰浣擄細

```json
{
  "modelVersion": "20260527_0000",
  "recallModelPath": "E:/End-To-End_Recommendation_System_X/data/model/recall_user_tower.pt",
  "rankingModelPath": "E:/End-To-End_Recommendation_System_X/data/model/ranking_mmoe.pt",
  "featureConfigPath": "E:/End-To-End_Recommendation_System_X/data/model/feature_config.json"
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "loaded": true
  }
}
```

## 5. 鍒嗛〉鍜屽埛鏂扮害瀹?
- 鍓嶇棣栨杩涘叆棣栭〉璋冪敤 `POST /recommendations/refresh`锛屽啀璋冪敤 `GET /recommendations/home` 鑾峰彇绗竴椤点€?- 鍓嶇鎺ヨ繎搴曢儴 200px 鏃惰皟鐢?`GET /recommendations/home` 鑾峰彇涓嬩竴椤点€?- 鍓嶇缁存姢 `displayedItemIds`锛岃繃婊ら噸澶嶅晢鍝併€?- 鍓嶇鎵嬪姩鍒锋柊璋冪敤 `POST /recommendations/refresh`锛屽苟娓呯┖鏈湴鎺ㄨ崘鍒楄〃銆?- 濡傛灉鍚庣杩斿洖 `hasMore=false`锛屽墠绔彲瑙﹀彂 `triggerType=exhausted` 鐨勫埛鏂般€?
## 琛ュ厖锛氳璇佷笌鐢ㄦ埛绠＄悊 API

### A.1 鐢ㄦ埛娉ㄥ唽

`POST /auth/register`

璇锋眰浣擄細

```json
{
  "username": "alice",
  "password": "Password123",
  "nickname": "Alice",
  "phone": "13800000000",
  "email": "alice@example.com"
}
```

鍝嶅簲锛?
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

閿欒鐮佽ˉ鍏咃細

| code | message | 璇存槑 |
| --- | --- | --- |
| 403001 | forbidden | 鏃犳潈闄愯闂?|
| 409001 | username_exists | 鐢ㄦ埛鍚嶅凡瀛樺湪 |
| 409002 | phone_exists | 鎵嬫満鍙峰凡瀛樺湪 |
| 423001 | user_disabled | 鐢ㄦ埛宸茶绂佺敤 |
| 423001 | account_locked | 璇ヨ处鍙疯繛缁?5 娆″瘑鐮侀敊璇悗閿佸畾 15 min |
| 429001 | too_many_login_attempts | 鍚?IP 鍦?5 min 鍐呯疮璁″け璐?鈮?30 娆?|

### A.2 鐢ㄦ埛鐧诲綍

`POST /auth/login`

璇锋眰浣擄細

```json
{
  "username": "alice",
  "password": "Password123"
}
```

鍝嶅簲锛?
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

### A.3 褰撳墠鐢ㄦ埛淇℃伅

`GET /users/me`

Header锛?
```text
Authorization: Bearer <accessToken>
```

鍝嶅簲锛?
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

### A.4 淇敼褰撳墠鐢ㄦ埛璧勬枡

`PUT /users/me`

璇锋眰浣擄細

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

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.5 淇敼瀵嗙爜

`PUT /users/me/password`

璇锋眰浣擄細

```json
{
  "oldPassword": "Password123",
  "newPassword": "Password456"
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.5.5 缁 access token

`POST /auth/refresh`

璇锋眰浣擄細

```json
{ "refreshToken": "<base64url>" }
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "accessToken": "jwt-token-here",
    "refreshToken": "<鏂?base64url>",
    "tokenType": "Bearer",
    "expiresIn": 7200,
    "refreshExpiresIn": 2592000,
    "user": { "userId": "u_10001", "username": "alice", "nickname": "Alice", "roles": ["USER"] }
  }
}
```

绾﹀畾锛?
- refresh token 涓€娆℃€э紝姣忔 refresh 閮戒細**鏃嬭浆**鍑烘柊鐨?refresh token锛屽墠绔繀椤绘浛鎹㈡湰鍦颁繚瀛樸€?- refresh token 榛樿 30 澶╋紝鐢?`app.auth.refreshTokenExpireDays` 鎺у埗銆?- 鐢ㄦ埛琚鐢ㄦ垨涓嶅瓨鍦?鈫?鎷掔粷 `401 invalid_refresh_token` / `423 user_disabled`銆?- 瑙﹀彂 `forceLogoutAll` 鏃讹紙绠＄悊鍛樼鐢?/ 鏀瑰瘑 / 璋冭鑹诧級锛岃鐢ㄦ埛鐨勬墍鏈?refresh token 涓€骞?revoke銆?
### A.6 閫€鍑虹櫥褰?
`POST /auth/logout`

璇存槑锛歁VP 鍙互鍙敱鍓嶇鍒犻櫎 token锛涘鏋滃惎鐢?Redis 榛戝悕鍗曪紝鍒欏悗绔皢 tokenId 鍐欏叆 `auth:blacklist:{tokenId}`銆?
鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.7 绠＄悊鍛樺垎椤垫煡璇㈢敤鎴?
`GET /admin/users`

鏉冮檺锛歚ADMIN`

璇锋眰鍙傛暟锛?
| 鍙傛暟 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
| --- | --- | --- | --- |
| keyword | string | 鍚?| 鐢ㄦ埛鍚嶃€佹樀绉般€佹墜鏈哄彿妯＄硦鏌ヨ |
| status | int | 鍚?| 1 姝ｅ父锛? 绂佺敤 |
| roleCode | string | 鍚?| `USER` 鎴?`ADMIN` |
| page | int | 鍚?| 椤电爜锛岄粯璁?1 |
| size | int | 鍚?| 姣忛〉鏁伴噺锛岄粯璁?20 |

鍝嶅簲锛?
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

### A.8 绠＄悊鍛樻洿鏂扮敤鎴风姸鎬?
`PUT /admin/users/{userId}/status`

鏉冮檺锛歚ADMIN`

璇锋眰浣擄細

```json
{
  "status": 0
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.9 绠＄悊鍛橀噸缃瘑鐮?
`PUT /admin/users/{userId}/password`

鏉冮檺锛歚ADMIN`

璇锋眰浣擄細

```json
{
  "newPassword": "Password123"
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.10 绠＄悊鍛樿皟鏁磋鑹?
`PUT /admin/users/{userId}/roles`

鏉冮檺锛歚ADMIN`

璇锋眰浣擄細

```json
{
  "roles": ["USER", "ADMIN"]
}
```

鍝嶅簲锛?
```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### A.11 涓庢帹鑽?API 鐨勭害瀹?
- 鐧诲綍鐢ㄦ埛璋冪敤鎺ㄨ崘鎺ュ彛鏃讹紝鍚庣浼樺厛浣跨敤 JWT 涓殑 `userId`銆?- 鏈櫥褰曟父瀹㈠彲浠ョ户缁€氳繃璇锋眰鍙傛暟浼?`userId`锛屼絾鍙兘浣滀负涓存椂娓稿 ID銆?- 绠＄悊鍛樻帴鍙ｇ粺涓€瑕佹眰 Header 涓惡甯?`Authorization: Bearer <accessToken>`锛屼笖 token 涓寘鍚?`ADMIN` 瑙掕壊銆?
### A.12 鐧诲綍闄愭祦绾﹀畾

| 瑙﹀彂 | 鍝嶅簲 code | 鎻愮ず |
| --- | --- | --- |
| 鍚屼竴 IP 5 min 鍐呯疮璁″け璐?鈮?30 娆?| `429001` | `too_many_login_attempts` |
| 鍚屼竴璐﹀彿杩炵画 5 娆″瘑鐮侀敊璇?| `423001` | `account_locked`锛堥攣瀹?15 min锛?|
| 鐧诲綍鎴愬姛 | 鈥?| 鑷姩娓呴櫎璇ヨ处鍙风殑澶辫触璁℃暟 |

闃堝€肩敱 `app.auth.loginRateLimit.*` 鎺у埗锛岃瑙?`10_楂樺苟鍙戣璁?md` 搂5銆?
### A.13 鐩戞帶绔偣

鍏紑锛堟棤闇€閴存潈锛夛細

| 璺緞 | 璇存槑 |
| --- | --- |
| `GET /actuator/health` | 鍋ュ悍妫€鏌ワ紱鍖呭惈 `inference` 鐔旀柇鍣ㄧ姸鎬?|
| `GET /actuator/circuitbreakers` | Resilience4j 鐔旀柇鍣ㄥ垪琛?+ 褰撳墠鐘舵€?|
| `GET /actuator/circuitbreakerevents/inference` | 鎺ㄧ悊鐔旀柇鍣ㄦ渶杩戜簨浠舵祦 |
| `GET /actuator/metrics/...` | 鎸囨爣锛堢嚎绋嬫睜闃熷垪闀垮害銆丠ikari 杩炴帴鏁般€丩ettuce 鍛戒护寤惰繜绛夛級 |
| `GET /actuator/prometheus` | Prometheus scrape 绔偣锛堝惈 trace / Hikari / HTTP / Tomcat 鎸囨爣锛?|
| `GET http://localhost:9000/metrics` | Python 鎺ㄧ悊 Prometheus锛堝惈 `recsys_recall_channel_*`銆乣recsys_rank_latency_ms`銆乣recsys_fallback_total`锛?|

### A.14 鍒嗗竷寮?trace

鍚庣姣忔鎺ㄧ悊璋冪敤閮戒細娉ㄥ叆 W3C `traceparent: 00-{traceId}-{spanId}-01`锛?
- Java 绔細Micrometer Tracing + OTEL锛沗@Observed("recommendation.refresh")` 鑷姩 span锛沗RestTemplate` interceptor 鑷姩鍐?header銆?- Python 绔細`TraceContextMiddleware` 瑙ｆ瀽 `traceparent`锛屾妸 `trace_id / span_id / request_id` 娉ㄥ叆鏃ュ織 context銆傚搷搴旈噷鍔?`x-trace-id` 璁╁墠绔兘閲囬泦銆?- 榛樿 OTLP 涓嶅鍑猴紙`otel.exporter.otlp.enabled=false`锛夈€傝瑙傛祴鏃堕儴缃?Jaeger / Tempo / Otel-Collector 鏀?`true`銆?