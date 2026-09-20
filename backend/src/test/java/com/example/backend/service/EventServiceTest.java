package com.example.backend.service;

import com.example.backend.common.BusinessException;
import com.example.backend.common.ErrorCode;
import com.example.backend.dto.EventReportRequest;
import com.example.backend.entity.BehaviorEvent;
import com.example.backend.entity.OutboxEvent;
import com.example.backend.mapper.BehaviorEventMapper;
import com.example.backend.mapper.OutboxEventMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class EventServiceTest {

    @Mock
    private BehaviorEventMapper behaviorEventMapper;

    @Mock
    private KafkaEventPublisher kafkaEventPublisher;

    @Mock
    private RedisCacheService redisCacheService;

    @Mock
    private OutboxEventMapper outboxEventMapper;

    @InjectMocks
    private EventService eventService;

    @Test
    void reportPersistsAllTrackingFields() {
        when(behaviorEventMapper.selectCount(any())).thenReturn(0L);
        when(kafkaEventPublisher.toPayload(any(BehaviorEvent.class))).thenReturn("{}");
        EventReportRequest request = new EventReportRequest(
                "evt-1",
                "user-1",
                "session-1",
                1001L,
                "expose",
                "home",
                3,
                "card_exposure",
                "req-1",
                "rec-1",
                1_700_000_000_000L
        );

        eventService.report(request);

        ArgumentCaptor<BehaviorEvent> captor = ArgumentCaptor.forClass(BehaviorEvent.class);
        verify(behaviorEventMapper).insert(captor.capture());
        BehaviorEvent event = captor.getValue();
        assertThat(event.getEventId()).isEqualTo("evt-1");
        assertThat(event.getItemId()).isEqualTo(1001L);
        assertThat(event.getEventType()).isEqualTo("expose");
        assertThat(event.getPosition()).isEqualTo(3);
        verify(outboxEventMapper).insert(any(OutboxEvent.class));
        verify(kafkaEventPublisher, never()).publish(any(BehaviorEvent.class));
        verify(redisCacheService, never()).delete(anyString());
    }

    @Test
    void reportRejectsDuplicateEventId() {
        when(behaviorEventMapper.selectCount(any())).thenReturn(1L);

        EventReportRequest request = new EventReportRequest(
                "evt-dup", "user-1", "session-1", 1001L, "click",
                "home", 1, "home_card", null, null, 1L
        );

        assertThatThrownBy(() -> eventService.report(request))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.EVENT_ID_EXISTS);
        verifyNoInteractions(kafkaEventPublisher);
    }

    @Test
    void clickInvalidatesHomeCache() {
        when(behaviorEventMapper.selectCount(any())).thenReturn(0L);
        when(kafkaEventPublisher.toPayload(any(BehaviorEvent.class))).thenReturn("{}");
        EventReportRequest request = new EventReportRequest(
                "evt-click", "user-1", "session-1", 1001L, "click",
                "home", 1, "home_card", null, null, 1L
        );

        eventService.report(request);

        verify(redisCacheService).delete("adrec:home:user-1");
    }
}
