package com.example.flink;

public record BehaviorEvent(
        String eventId,
        String userId,
        String sessionId,
        Long itemId,
        String eventType,
        String page,
        Integer position,
        String source,
        String requestId,
        String recommendationId,
        Long eventTime
) {
}
