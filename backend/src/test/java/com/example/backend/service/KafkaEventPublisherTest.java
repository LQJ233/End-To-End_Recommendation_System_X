package com.example.backend.service;

import com.example.backend.entity.BehaviorEvent;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.kafka.core.KafkaTemplate;

import java.util.concurrent.CompletableFuture;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class KafkaEventPublisherTest {

    @Mock
    private KafkaTemplate<String, String> kafkaTemplate;

    private ObjectMapper objectMapper;
    private KafkaEventPublisher publisher;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        publisher = new KafkaEventPublisher(kafkaTemplate, objectMapper, "behavior-events");
    }

    @Test
    void publishSendsSnakeCaseTrackingPayload() throws Exception {
        when(kafkaTemplate.send(anyString(), anyString(), anyString()))
                .thenReturn(CompletableFuture.completedFuture(null));
        BehaviorEvent event = new BehaviorEvent();
        event.setEventId("evt-1");
        event.setUserId("user-1");
        event.setSessionId("session-1");
        event.setItemId(1001L);
        event.setEventType("expose");
        event.setPage("home");
        event.setPosition(1);
        event.setSource("card_exposure");
        event.setRequestId("req-1");
        event.setRecommendationId("rec-1");
        event.setEventTime(1_700_000_000_000L);

        boolean published = publisher.publish(event);

        assertThat(published).isTrue();
        ArgumentCaptor<String> payloadCaptor = ArgumentCaptor.forClass(String.class);
        verify(kafkaTemplate).send(
                org.mockito.ArgumentMatchers.eq("behavior-events"),
                org.mockito.ArgumentMatchers.eq("evt-1"),
                payloadCaptor.capture()
        );
        JsonNode payload = objectMapper.readTree(payloadCaptor.getValue());
        assertThat(payload.get("event_id").asText()).isEqualTo("evt-1");
        assertThat(payload.get("user_id").asText()).isEqualTo("user-1");
        assertThat(payload.get("item_id").asLong()).isEqualTo(1001L);
        assertThat(payload.get("event_type").asText()).isEqualTo("expose");
    }

    @Test
    void publishDoesNotBreakRequestWhenKafkaIsUnavailable() {
        when(kafkaTemplate.send(anyString(), anyString(), anyString()))
                .thenThrow(new RuntimeException("kafka down"));
        BehaviorEvent event = new BehaviorEvent();
        event.setEventId("evt-2");
        event.setUserId("user-1");
        event.setSessionId("session-1");
        event.setEventType("click");
        event.setPage("home");
        event.setSource("home_card");
        event.setEventTime(1L);

        assertThat(publisher.publish(event)).isFalse();
    }
}
