package com.example.backend.config;

import com.example.backend.service.RecServingClient;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component
public class RecServingHealthIndicator implements HealthIndicator {

    private final RecServingClient recServingClient;

    public RecServingHealthIndicator(RecServingClient recServingClient) {
        this.recServingClient = recServingClient;
    }

    @Override
    public Health health() {
        boolean available = recServingClient.isHealthy();
        return Health.up()
                .withDetail("recServingAvailable", available)
                .build();
    }
}
