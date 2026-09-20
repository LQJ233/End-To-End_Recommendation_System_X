package com.example.flink;

import redis.clients.jedis.JedisPooled;

public class RedisFeatureStore implements FeatureStore {

    private static final int USER_HISTORY_LIMIT = 49;
    private static final int HOT_ITEM_LIMIT = 999;

    private final JedisPooled jedis;

    public RedisFeatureStore(String host, int port) {
        this(new JedisPooled(host, port));
    }

    RedisFeatureStore(JedisPooled jedis) {
        this.jedis = jedis;
    }

    @Override
    public void addUserHistory(String userId, long itemId) {
        String key = "adrec:user:history:" + userId;
        jedis.lrem(key, 0, String.valueOf(itemId));
        jedis.lpush(key, String.valueOf(itemId));
        jedis.ltrim(key, 0, USER_HISTORY_LIMIT);
    }

    @Override
    public void markHotItem(long itemId) {
        jedis.lrem("adrec:hot:items", 0, String.valueOf(itemId));
        jedis.lpush("adrec:hot:items", String.valueOf(itemId));
        jedis.ltrim("adrec:hot:items", 0, HOT_ITEM_LIMIT);
    }

    @Override
    public void incrementUserFeature(String userId, String field, long delta) {
        jedis.hincrBy("adrec:user:features:" + userId, field, delta);
    }

    @Override
    public void updateUserWindowFeature(
            String userId,
            long clickCount,
            long distinctItemCount,
            long lastClickTime,
            long windowEnd
    ) {
        String key = "adrec:user:features:" + userId;
        jedis.hset(key, "click_count_window", String.valueOf(clickCount));
        jedis.hset(key, "distinct_item_count_window", String.valueOf(distinctItemCount));
        jedis.hset(key, "last_click_time", String.valueOf(lastClickTime));
        jedis.hset(key, "feature_window_end", String.valueOf(windowEnd));
        jedis.expire(key, 86_400);
    }

    @Override
    public void addRealtimeHotItem(long itemId, long clickCount, long windowEnd) {
        String key = "adrec:hot:items:realtime";
        jedis.zadd(key, clickCount, String.valueOf(itemId));
        jedis.expire(key, 3_600);
    }

    @Override
    public void close() {
        jedis.close();
    }
}
