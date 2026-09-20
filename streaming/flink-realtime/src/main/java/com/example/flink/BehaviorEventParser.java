package com.example.flink;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;

import java.io.Serializable;

public class BehaviorEventParser implements Serializable {

    private transient ObjectMapper objectMapper;

    private ObjectMapper mapper() {
        if (objectMapper == null) {
            objectMapper = new ObjectMapper()
                    .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
                    .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        }
        return objectMapper;
    }

    public BehaviorEvent parse(String json) {
        try {
            JsonNode node = mapper().readTree(json);
            requireText(node, "event_id");
            requireText(node, "user_id");
            requireText(node, "session_id");
            requireText(node, "event_type");
            requireText(node, "page");
            requireText(node, "source");
            requireNumber(node, "event_time");
            return new BehaviorEvent(
                    node.get("event_id").asText(),
                    node.get("user_id").asText(),
                    node.get("session_id").asText(),
                    optionalLong(node, "item_id"),
                    node.get("event_type").asText(),
                    node.get("page").asText(),
                    optionalInt(node, "position"),
                    node.get("source").asText(),
                    optionalText(node, "request_id"),
                    optionalText(node, "recommendation_id"),
                    node.get("event_time").asLong()
            );
        } catch (IllegalArgumentException exception) {
            throw exception;
        } catch (Exception exception) {
            throw new IllegalArgumentException("invalid behavior event json", exception);
        }
    }

    public String toJson(BehaviorEvent event) {
        try {
            return mapper().writeValueAsString(event);
        } catch (Exception exception) {
            throw new IllegalStateException("failed to serialize behavior event", exception);
        }
    }

    private static void requireText(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull() || value.asText().isBlank()) {
            throw new IllegalArgumentException("missing required field: " + field);
        }
    }

    private static void requireNumber(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull() || !value.isNumber()) {
            throw new IllegalArgumentException("missing numeric field: " + field);
        }
    }

    private static Long optionalLong(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? null : value.asLong();
    }

    private static Integer optionalInt(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? null : value.asInt();
    }

    private static String optionalText(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? null : value.asText();
    }
}
