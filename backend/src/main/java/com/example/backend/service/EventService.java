package com.example.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.backend.common.BusinessException;
import com.example.backend.common.ErrorCode;
import com.example.backend.dto.EventReportRequest;
import com.example.backend.entity.BehaviorEvent;
import com.example.backend.entity.OutboxEvent;
import com.example.backend.mapper.BehaviorEventMapper;
import com.example.backend.mapper.OutboxEventMapper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Set;

@Service
public class EventService {

    private static final Set<String> INTEREST_EVENTS = Set.of(
            "click",
            "detail_view",
            "add_cart"
    );

    private final BehaviorEventMapper behaviorEventMapper;
    private final KafkaEventPublisher kafkaEventPublisher;
    private final RedisCacheService redisCacheService;
    private final OutboxEventMapper outboxEventMapper;

    public EventService(
            BehaviorEventMapper behaviorEventMapper,
            KafkaEventPublisher kafkaEventPublisher,
            RedisCacheService redisCacheService,
            OutboxEventMapper outboxEventMapper
    ) {
        this.behaviorEventMapper = behaviorEventMapper;
        this.kafkaEventPublisher = kafkaEventPublisher;
        this.redisCacheService = redisCacheService;
        this.outboxEventMapper = outboxEventMapper;
    }

    public void report(EventReportRequest request) {
        Long count = behaviorEventMapper.selectCount(new LambdaQueryWrapper<BehaviorEvent>()
                .eq(BehaviorEvent::getEventId, request.eventId()));
        if (count > 0) {
            throw new BusinessException(ErrorCode.EVENT_ID_EXISTS);
        }

        BehaviorEvent event = new BehaviorEvent();
        event.setEventId(request.eventId());
        event.setUserId(request.userId());
        event.setSessionId(request.sessionId());
        event.setItemId(request.itemId());
        event.setEventType(request.eventType());
        event.setPage(request.page());
        event.setPosition(request.position());
        event.setSource(request.source());
        event.setRequestId(request.requestId());
        event.setRecommendationId(request.recommendationId());
        event.setEventTime(request.eventTime());
        behaviorEventMapper.insert(event);

        OutboxEvent outboxEvent = new OutboxEvent();
        outboxEvent.setEventId(event.getEventId());
        outboxEvent.setPayload(kafkaEventPublisher.toPayload(event));
        outboxEvent.setStatus("PENDING");
        outboxEvent.setRetryCount(0);
        outboxEvent.setNextRetryAt(LocalDateTime.now());
        outboxEventMapper.insert(outboxEvent);

        if (INTEREST_EVENTS.contains(request.eventType())) {
            redisCacheService.delete("adrec:home:" + request.userId());
        }
    }
}
