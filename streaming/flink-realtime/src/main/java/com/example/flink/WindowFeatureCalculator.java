package com.example.flink;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class WindowFeatureCalculator {

    private WindowFeatureCalculator() {
    }

    public static UserWindowFeature userFeature(List<BehaviorEvent> events) {
        Set<Long> itemIds = new HashSet<>();
        long lastClickTime = 0L;
        for (BehaviorEvent event : events) {
            if (event.itemId() != null) {
                itemIds.add(event.itemId());
            }
            if (event.eventTime() != null) {
                lastClickTime = Math.max(lastClickTime, event.eventTime());
            }
        }
        return new UserWindowFeature(events.size(), itemIds.size(), lastClickTime);
    }

    public static long itemClickCount(List<BehaviorEvent> events, long itemId) {
        return events.stream()
                .filter(event -> event.itemId() != null && event.itemId() == itemId)
                .count();
    }

    public record UserWindowFeature(
            long clickCount,
            long distinctItemCount,
            long lastClickTime
    ) {
    }
}
