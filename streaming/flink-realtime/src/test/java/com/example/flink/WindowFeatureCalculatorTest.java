package com.example.flink;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class WindowFeatureCalculatorTest {

    @Test
    void calculatesUserClickAndDistinctItemCounts() {
        List<BehaviorEvent> events = List.of(
                event("evt-1", "user-1", 10L, 1000L),
                event("evt-2", "user-1", 20L, 2000L),
                event("evt-3", "user-1", 10L, 3000L)
        );

        WindowFeatureCalculator.UserWindowFeature feature =
                WindowFeatureCalculator.userFeature(events);

        assertThat(feature.clickCount()).isEqualTo(3);
        assertThat(feature.distinctItemCount()).isEqualTo(2);
        assertThat(feature.lastClickTime()).isEqualTo(3000L);
    }

    @Test
    void calculatesItemClickCount() {
        List<BehaviorEvent> events = List.of(
                event("evt-1", "user-1", 10L, 1000L),
                event("evt-2", "user-2", 10L, 2000L),
                event("evt-3", "user-1", 20L, 3000L)
        );

        assertThat(WindowFeatureCalculator.itemClickCount(events, 10L)).isEqualTo(2);
    }

    private static BehaviorEvent event(
            String eventId,
            String userId,
            long itemId,
            long eventTime
    ) {
        return new BehaviorEvent(
                eventId,
                userId,
                "session",
                itemId,
                "click",
                "home",
                1,
                "home_card",
                "request",
                "recommendation",
                eventTime
        );
    }
}
