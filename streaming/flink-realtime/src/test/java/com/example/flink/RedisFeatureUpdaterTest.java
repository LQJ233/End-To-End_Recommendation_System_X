package com.example.flink;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class RedisFeatureUpdaterTest {

    @Test
    void clickUpdatesHistoryHotItemsAndClickCount() {
        InMemoryFeatureStore store = new InMemoryFeatureStore();
        RedisFeatureUpdater updater = new RedisFeatureUpdater(store);

        updater.update(new BehaviorEvent(
                "evt-1", "user-1", "session-1", 1001L, "click",
                "home", 1, "home_card", "req-1", "rec-1", 1L
        ));

        assertThat(store.calls).containsExactly(
                "history:user-1:1001",
                "hot:1001",
                "feature:user-1:click_count:1"
        );
    }

    @Test
    void exposeDoesNotChangeOnlineInterestFeatures() {
        InMemoryFeatureStore store = new InMemoryFeatureStore();
        RedisFeatureUpdater updater = new RedisFeatureUpdater(store);

        updater.update(new BehaviorEvent(
                "evt-2", "user-1", "session-1", 1001L, "expose",
                "home", 1, "card_exposure", "req-1", "rec-1", 1L
        ));

        assertThat(store.calls).isEmpty();
    }

    private static final class InMemoryFeatureStore implements FeatureStore {
        private final List<String> calls = new ArrayList<>();

        @Override
        public void addUserHistory(String userId, long itemId) {
            calls.add("history:" + userId + ":" + itemId);
        }

        @Override
        public void markHotItem(long itemId) {
            calls.add("hot:" + itemId);
        }

        @Override
        public void incrementUserFeature(String userId, String field, long delta) {
            calls.add("feature:" + userId + ":" + field + ":" + delta);
        }

        @Override
        public void updateUserWindowFeature(
                String userId,
                long clickCount,
                long distinctItemCount,
                long lastClickTime,
                long windowEnd
        ) {
            calls.add("window:" + userId + ":" + clickCount);
        }

        @Override
        public void addRealtimeHotItem(long itemId, long clickCount, long windowEnd) {
            calls.add("hot-window:" + itemId + ":" + clickCount);
        }
    }
}
