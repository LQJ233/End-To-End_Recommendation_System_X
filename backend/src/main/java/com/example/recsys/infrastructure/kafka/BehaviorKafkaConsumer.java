package com.example.recsys.infrastructure.kafka;

import com.example.recsys.domain.entity.RecBehaviorLog;
import com.example.recsys.infrastructure.mysql.RecBehaviorLogMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

/** Consumes user_behavior_log from Kafka and buffers rows for batched MySQL inserts. */
@Component
public class BehaviorKafkaConsumer {
    private static final Logger log = LoggerFactory.getLogger(BehaviorKafkaConsumer.class);
    private static final int FLUSH_THRESHOLD = 500;

    private final RecBehaviorLogMapper mapper;
    private final ObjectMapper json = new ObjectMapper();
    private final ConcurrentLinkedQueue<RecBehaviorLog> buffer = new ConcurrentLinkedQueue<>();

    public BehaviorKafkaConsumer(RecBehaviorLogMapper mapper) {
        this.mapper = mapper;
    }

    @KafkaListener(topics = "${app.kafka.behaviorTopic}",
                   groupId = "${app.kafka.consumerGroup}",
                   batch = "true")
    public void consume(List<String> records) {
        for (String raw : records) {
            try {
                JsonNode n = json.readTree(raw);
                RecBehaviorLog row = new RecBehaviorLog();
                row.setUserId(n.path("userId").asText());
                row.setItemId(n.path("itemId").asText());
                row.setBehaviorType(n.path("behaviorType").asInt());
                row.setTimestamp(n.path("timestamp").asLong(System.currentTimeMillis()));
                row.setRequestId(n.path("requestId").asText(null));
                row.setScene(n.path("scene").asText(null));
                row.setSource(n.path("source").asText("kafka"));
                buffer.offer(row);
            } catch (Exception e) {
                log.warn("bad behavior payload: {}", e.getMessage());
            }
        }
        if (buffer.size() >= FLUSH_THRESHOLD) flush();
    }

    public synchronized int flush() {
        if (buffer.isEmpty()) return 0;
        List<RecBehaviorLog> batch = new ArrayList<>(buffer.size());
        RecBehaviorLog r;
        while ((r = buffer.poll()) != null) batch.add(r);
        try {
            mapper.batchInsert(batch);
            log.info("flushed behavior batch size={}", batch.size());
        } catch (Exception e) {
            log.error("flush failed, requeueing {} rows: {}", batch.size(), e.getMessage());
            buffer.addAll(batch);
            return 0;
        }
        return batch.size();
    }
}
