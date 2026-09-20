package com.example.flink;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.sink.DiscardingSink;
import org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;

public class BehaviorRealtimeJob {

    public static void main(String[] args) throws Exception {
        String bootstrapServers = env("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092");
        String behaviorTopic = env("BEHAVIOR_TOPIC", "behavior-events");
        String redisHost = env("REDIS_HOST", "127.0.0.1");
        int redisPort = Integer.parseInt(env("REDIS_PORT", "6379"));
        String minioPath = env(
                "MINIO_REALTIME_PATH",
                "s3a://warehouse/realtime/behavior_events"
        );
        int featureWindowSeconds = Integer.parseInt(env("FEATURE_WINDOW_SECONDS", "60"));

        StreamExecutionEnvironment environment = StreamExecutionEnvironment.getExecutionEnvironment();
        environment.setParallelism(1);
        environment.enableCheckpointing(10_000L);

        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers(bootstrapServers)
                .setTopics(behaviorTopic)
                .setGroupId("flink-behavior-realtime")
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        BehaviorEventParser parser = new BehaviorEventParser();
        DataStream<BehaviorEvent> events = environment
                .fromSource(source, WatermarkStrategy.noWatermarks(), "behavior-events")
                .map(parser::parse)
                .name("parse-behavior-event");

        events.addSink(new RedisFeatureSink(redisHost, redisPort))
                .name("redis-feature-sink");

        events.addSink(new MinioRawJsonSink(minioPath)).name("minio-raw-sink");

        DataStream<BehaviorEvent> clickEvents = events.filter(
                event -> "click".equals(event.eventType()) && event.itemId() != null
        );
        clickEvents
                .keyBy(BehaviorEvent::userId)
                .window(TumblingProcessingTimeWindows.of(Time.seconds(featureWindowSeconds)))
                .process(new UserWindowFeatureFunction(redisHost, redisPort))
                .name("user-window-features")
                .addSink(new DiscardingSink<>());
        clickEvents
                .keyBy(BehaviorEvent::itemId)
                .window(TumblingProcessingTimeWindows.of(Time.seconds(featureWindowSeconds)))
                .process(new ItemWindowFeatureFunction(redisHost, redisPort))
                .name("item-window-features")
                .addSink(new DiscardingSink<>());

        environment.execute("behavior-realtime-job");
    }

    private static String env(String name, String defaultValue) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? defaultValue : value;
    }
}
