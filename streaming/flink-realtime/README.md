# Flink Realtime

本模块使用 Flink 1.20.5 的 Maven 依赖和本地 MiniCluster，不要求安装独立 Flink 发行版。

## 依赖

```text
Flink 1.20.5
flink-connector-kafka 3.4.0-1.20
flink-connector-mysql-cdc 3.6.0-1.20
Jedis 5.2.0
Java 17
```

## 构建

```bash
export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
export PATH="$JAVA_HOME/bin:$PATH"
mvn -s maven-settings.xml package -DskipTests
```

产物：

```text
target/flink-realtime-0.0.1-SNAPSHOT.jar
```

## 作业

行为实时作业：

```bash
java -cp target/flink-realtime-0.0.1-SNAPSHOT.jar \
  com.example.flink.BehaviorRealtimeJob
```

处理链路：

```text
Kafka behavior-events
-> Redis adrec:user:history:{user_id}
-> Redis adrec:hot:items
-> Redis adrec:user:features:{user_id}
-> MinIO s3a://warehouse/realtime/behavior_events
```

MySQL CDC 作业：

```bash
java -cp target/flink-realtime-0.0.1-SNAPSHOT.jar \
  com.example.flink.MySqlCdcJob
```

处理链路：

```text
MySQL ecommerce.behavior_event binlog
-> Kafka mysql-cdc-ecommerce
```

## 本地约定

```text
Kafka：127.0.0.1:9092
Redis：127.0.0.1:6379
MySQL：127.0.0.1:3306
MinIO：http://127.0.0.1:9000
```

完整启动、停止和验证脚本见项目根目录 `scripts/`。
