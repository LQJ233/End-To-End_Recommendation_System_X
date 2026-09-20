package com.example.flink;

import java.io.Serializable;
import java.util.Set;

public class RedisFeatureUpdater implements Serializable {

    private static final Set<String> INTEREST_EVENTS = Set.of(
            "click",
            "detail_view",
            "add_cart"
    );

    private final FeatureStore featureStore;

    public RedisFeatureUpdater(FeatureStore featureStore) {
        this.featureStore = featureStore;
    }

    public void update(BehaviorEvent event) {
        if (event == null
                || event.userId() == null
                || event.itemId() == null
                || !INTEREST_EVENTS.contains(event.eventType())) {
            return;
        }
        featureStore.addUserHistory(event.userId(), event.itemId());
        featureStore.markHotItem(event.itemId());
        featureStore.incrementUserFeature(event.userId(), "click_count", 1L);
    }
}
