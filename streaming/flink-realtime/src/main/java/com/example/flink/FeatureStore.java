package com.example.flink;

public interface FeatureStore extends AutoCloseable {

    void addUserHistory(String userId, long itemId);

    void markHotItem(long itemId);

    void incrementUserFeature(String userId, String field, long delta);

    void updateUserWindowFeature(
            String userId,
            long clickCount,
            long distinctItemCount,
            long lastClickTime,
            long windowEnd
    );

    void addRealtimeHotItem(long itemId, long clickCount, long windowEnd);

    @Override
    default void close() {
    }
}
