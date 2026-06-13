package com.example.recsys.scheduler;

import com.example.recsys.infrastructure.kafka.BehaviorKafkaConsumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class BehaviorBatchFlushScheduler {
    private static final Logger log = LoggerFactory.getLogger(BehaviorBatchFlushScheduler.class);
    private final BehaviorKafkaConsumer consumer;

    public BehaviorBatchFlushScheduler(BehaviorKafkaConsumer consumer) {
        this.consumer = consumer;
    }

    @Scheduled(fixedDelay = 30_000L)
    public void periodic() {
        int n = consumer.flush();
        if (n > 0) log.debug("periodic flush wrote {} rows", n);
    }

    @Scheduled(cron = "0 0 0 * * *")
    public void nightly() {
        int n = consumer.flush();
        log.info("nightly flush wrote {} rows", n);
    }
}
