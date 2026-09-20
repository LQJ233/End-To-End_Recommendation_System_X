package com.example.backend.service;

import com.example.backend.entity.BehaviorEvent;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Component
public class KafkaEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(KafkaEventPublisher.class);

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final String topic;

    public KafkaEventPublisher(
            KafkaTemplate<String, String> kafkaTemplate,
            ObjectMapper objectMapper,
            @Value("${kafka.topics.behavior-events}") String topic
    ) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
        this.topic = topic;
    }

    public String toPayload(BehaviorEvent event) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("event_id", event.getEventId());
        payload.put("user_id", event.getUserId());
        payload.put("session_id", event.getSessionId());
        payload.put("item_id", event.getItemId());
        payload.put("event_type", event.getEventType());
        payload.put("page", event.getPage());
        payload.put("position", event.getPosition());
        payload.put("source", event.getSource());
        payload.put("request_id", event.getRequestId());
        payload.put("recommendation_id", event.getRecommendationId());
        payload.put("event_time", event.getEventTime());

        try {
            return objectMapper.writeValueAsString(payload);
        } catch (Exception exception) {
            log.warn(
                    "Failed to build Kafka payload for event {}: {}",
                    event.getEventId(),
                    exception.getMessage()
            );
            return null;
        }
    }

    public boolean publish(BehaviorEvent event) {
        return publishRaw(event.getEventId(), toPayload(event));
    }

    public boolean publishRaw(String eventId, String payload) {
        if (payload == null) {
            return false;
        }
        try {
            kafkaTemplate.send(topic, eventId, payload).get(2, TimeUnit.SECONDS);
            return true;
        } catch (Exception exception) {
            log.warn(
                    "Failed to publish behavior event {}: {}",
                    eventId,
                    exception.getMessage()
            );
            return false;
        }
    }
}
