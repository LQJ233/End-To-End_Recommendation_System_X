package com.example.flink;

import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import java.util.ArrayList;
import java.util.List;

public class ItemWindowFeatureFunction
        extends ProcessWindowFunction<BehaviorEvent, String, Long, TimeWindow> {

    private final String redisHost;
    private final int redisPort;
    private transient RedisFeatureStore featureStore;

    public ItemWindowFeatureFunction(String redisHost, int redisPort) {
        this.redisHost = redisHost;
        this.redisPort = redisPort;
    }

    @Override
    public void open(Configuration parameters) {
        featureStore = new RedisFeatureStore(redisHost, redisPort);
    }

    @Override
    public void process(
            Long itemId,
            Context context,
            Iterable<BehaviorEvent> events,
            Collector<String> out
    ) {
        List<BehaviorEvent> eventList = new ArrayList<>();
        events.forEach(eventList::add);
        long clickCount = WindowFeatureCalculator.itemClickCount(eventList, itemId);
        featureStore.addRealtimeHotItem(itemId, clickCount, context.window().getEnd());
        out.collect(String.valueOf(itemId));
    }

    @Override
    public void close() {
        if (featureStore != null) {
            featureStore.close();
        }
    }
}
