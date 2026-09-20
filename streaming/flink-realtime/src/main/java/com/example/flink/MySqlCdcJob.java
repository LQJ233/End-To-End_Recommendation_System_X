package com.example.flink;

import org.apache.flink.cdc.connectors.mysql.source.MySqlSource;
import org.apache.flink.cdc.connectors.mysql.table.StartupOptions;
import org.apache.flink.cdc.debezium.JsonDebeziumDeserializationSchema;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.base.DeliveryGuarantee;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.util.List;

public class MySqlCdcJob {

    public static final List<String> TABLES = List.of(
            "ecommerce.behavior_event",
            "ecommerce.item",
            "ecommerce.user",
            "ecommerce.recommendation_log",
            "ecommerce.model_registry",
            "ecommerce.event_outbox",
            "ecommerce.pipeline_watermark"
    );

    public static void main(String[] args) throws Exception {
        String bootstrapServers = env("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092");
        String cdcTopic = env("MYSQL_CDC_TOPIC", "mysql-cdc-ecommerce");

        MySqlSource<String> source = MySqlSource.<String>builder()
                .hostname(env("MYSQL_HOST", "127.0.0.1"))
                .port(Integer.parseInt(env("MYSQL_PORT", "3306")))
                .databaseList("ecommerce")
                .tableList(TABLES.toArray(String[]::new))
                .username(env("MYSQL_USER", "root"))
                .password(env("MYSQL_PASSWORD", ""))
                .startupOptions(StartupOptions.initial())
                .deserializer(new JsonDebeziumDeserializationSchema())
                .build();

        KafkaSink<String> sink = KafkaSink.<String>builder()
                .setBootstrapServers(bootstrapServers)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.<String>builder()
                                .setTopic(cdcTopic)
                                .setValueSerializationSchema(new SimpleStringSchema())
                                .build()
                )
                .setDeliveryGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
                .build();

        StreamExecutionEnvironment environment = StreamExecutionEnvironment.getExecutionEnvironment();
        environment.enableCheckpointing(10_000L);
        environment
                .fromSource(source, WatermarkStrategy.noWatermarks(), "mysql-cdc-ecommerce")
                .sinkTo(sink)
                .name("kafka-cdc-sink");
        environment.execute("mysql-cdc-ecommerce-job");
    }

    private static String env(String name, String defaultValue) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? defaultValue : value;
    }
}
