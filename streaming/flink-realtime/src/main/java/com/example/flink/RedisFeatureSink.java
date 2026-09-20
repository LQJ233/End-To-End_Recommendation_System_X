package com.example.flink;

import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.sink.RichSinkFunction;

public class RedisFeatureSink extends RichSinkFunction<BehaviorEvent> {

    private final String redisHost;
    private final int redisPort;
    private transient RedisFeatureStore featureStore;
    private transient RedisFeatureUpdater featureUpdater;

    public RedisFeatureSink(String redisHost, int redisPort) {
        this.redisHost = redisHost;
        this.redisPort = redisPort;
    }

    @Override
    public void open(Configuration parameters) {
        featureStore = new RedisFeatureStore(redisHost, redisPort);
        featureUpdater = new RedisFeatureUpdater(featureStore);
    }

    @Override
    public void invoke(BehaviorEvent event, Context context) {
        featureUpdater.update(event);
    }

    @Override
    public void close() {
        if (featureStore != null) {
            featureStore.close();
        }
    }
}
