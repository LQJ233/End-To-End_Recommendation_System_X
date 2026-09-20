package com.example.backend.service;

import com.example.backend.entity.OutboxEvent;
import com.example.backend.mapper.OutboxEventMapper;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class OutboxPublisherJobTest {

    private final OutboxEventMapper mapper = mock(OutboxEventMapper.class);
    private final KafkaEventPublisher publisher = mock(KafkaEventPublisher.class);
    private final OutboxPublisherJob job = new OutboxPublisherJob(mapper, publisher, 3);

    @Test
    void marksEventSentAfterSuccessfulPublish() {
        OutboxEvent event = pendingEvent(0);
        when(mapper.selectList(any())).thenReturn(List.of(event));
        when(publisher.publishRaw("evt-1", "{}")).thenReturn(true);

        int published = job.publishPending();

        assertThat(published).isEqualTo(1);
        assertThat(event.getStatus()).isEqualTo("SENT");
        verify(mapper).updateById(event);
    }

    @Test
    void schedulesRetryAfterFailure() {
        OutboxEvent event = pendingEvent(0);
        when(mapper.selectList(any())).thenReturn(List.of(event));
        when(publisher.publishRaw("evt-1", "{}")).thenReturn(false);

        job.publishPending();

        assertThat(event.getStatus()).isEqualTo("PENDING");
        assertThat(event.getRetryCount()).isEqualTo(1);
        assertThat(event.getNextRetryAt()).isAfter(LocalDateTime.now());
    }

    @Test
    void marksEventDeadAfterMaxRetries() {
        OutboxEvent event = pendingEvent(2);
        when(mapper.selectList(any())).thenReturn(List.of(event));
        when(publisher.publishRaw("evt-1", "{}")).thenReturn(false);

        job.publishPending();

        assertThat(event.getStatus()).isEqualTo("DEAD");
        assertThat(event.getRetryCount()).isEqualTo(3);
    }

    private static OutboxEvent pendingEvent(int retryCount) {
        OutboxEvent event = new OutboxEvent();
        event.setId(1L);
        event.setEventId("evt-1");
        event.setPayload("{}");
        event.setStatus("PENDING");
        event.setRetryCount(retryCount);
        event.setNextRetryAt(LocalDateTime.now().minusSeconds(1));
        return event;
    }
}
