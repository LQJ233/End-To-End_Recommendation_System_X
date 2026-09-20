package com.example.flink;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BehaviorEventParserTest {

    private final BehaviorEventParser parser = new BehaviorEventParser();

    @Test
    void parseMapsSnakeCasePayload() {
        BehaviorEvent event = parser.parse("""
                {
                  "event_id":"evt-1",
                  "user_id":"user-1",
                  "session_id":"session-1",
                  "item_id":1001,
                  "event_type":"click",
                  "page":"home",
                  "position":2,
                  "source":"home_card",
                  "request_id":"req-1",
                  "recommendation_id":"rec-1",
                  "event_time":1700000000000
                }
                """);

        assertThat(event.eventId()).isEqualTo("evt-1");
        assertThat(event.itemId()).isEqualTo(1001L);
        assertThat(event.eventType()).isEqualTo("click");
        assertThat(event.position()).isEqualTo(2);
    }

    @Test
    void parseRejectsMissingEventId() {
        assertThatThrownBy(() -> parser.parse("""
                {"user_id":"user-1","event_type":"click","page":"home","source":"home_card","event_time":1}
                """))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("event_id");
    }

    @Test
    void toJsonKeepsSnakeCaseFields() {
        String json = parser.toJson(new BehaviorEvent(
                "evt-1", "user-1", "session-1", 1001L, "click",
                "home", 1, "home_card", "req-1", "rec-1", 1L
        ));

        assertThat(json).contains("\"event_id\":\"evt-1\"");
        assertThat(json).contains("\"item_id\":1001");
    }
}
