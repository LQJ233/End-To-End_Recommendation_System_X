package com.example.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.backend.entity.OutboxEvent;
import com.example.backend.mapper.OutboxEventMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Component
public class OutboxPublisherJob {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisherJob.class);

    private final OutboxEventMapper outboxEventMapper;
    private final KafkaEventPublisher kafkaEventPublisher;
    private final int maxRetries;

    public OutboxPublisherJob(
            OutboxEventMapper outboxEventMapper,
            KafkaEventPublisher kafkaEventPublisher,
            @Value("${outbox.max-retries:10}") int maxRetries
    ) {
        this.outboxEventMapper = outboxEventMapper;
        this.kafkaEventPublisher = kafkaEventPublisher;
        this.maxRetries = maxRetries;
    }

    @Scheduled(fixedDelayString = "${outbox.publish-interval-ms:2000}")
    @Transactional
    public int publishPending() {
        List<OutboxEvent> pendingEvents = outboxEventMapper.selectList(
                new LambdaQueryWrapper<OutboxEvent>()
                        .eq(OutboxEvent::getStatus, "PENDING")
                        .le(OutboxEvent::getNextRetryAt, LocalDateTime.now())
                        .orderByAsc(OutboxEvent::getId)
                        .last("LIMIT 100")
        );

        int published = 0;
        for (OutboxEvent event : pendingEvents) {
            boolean success = kafkaEventPublisher.publishRaw(event.getEventId(), event.getPayload());
            if (success) {
                event.setStatus("SENT");
                published++;
            } else {
                handleFailure(event);
            }
            outboxEventMapper.updateById(event);
        }
        if (published > 0) {
            log.info("Published {} outbox events", published);
        }
        return published;
    }

    private void handleFailure(OutboxEvent event) {
        int retryCount = event.getRetryCount() == null ? 0 : event.getRetryCount();
        retryCount++;
        event.setRetryCount(retryCount);
        if (retryCount >= maxRetries) {
            event.setStatus("DEAD");
            return;
        }
        long delaySeconds = Math.min(60L, 1L << Math.min(retryCount, 6));
        event.setNextRetryAt(LocalDateTime.now().plusSeconds(delaySeconds));
    }
}
