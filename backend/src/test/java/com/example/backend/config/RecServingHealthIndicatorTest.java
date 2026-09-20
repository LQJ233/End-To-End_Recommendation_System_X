package com.example.backend.config;

import com.example.backend.service.RecServingClient;
import org.junit.jupiter.api.Test;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.Status;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class RecServingHealthIndicatorTest {

    @Test
    void healthKeepsApplicationUpWhenRecServingIsDown() {
        RecServingClient client = mock(RecServingClient.class);
        when(client.isHealthy()).thenReturn(false);
        RecServingHealthIndicator indicator = new RecServingHealthIndicator(client);

        Health health = indicator.health();

        assertThat(health.getStatus()).isEqualTo(Status.UP);
        assertThat(health.getDetails().get("recServingAvailable")).isEqualTo(false);
    }
}
