package com.example.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class RecServingClient {

    private final String baseUrl;
    private final int maxAttempts;
    private final int failureThreshold;
    private final long openDurationMs;
    private final int readTimeoutMs;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final MeterRegistry meterRegistry;

    private final AtomicInteger consecutiveFailures = new AtomicInteger();
    private final AtomicLong openUntilEpochMs = new AtomicLong();

    public RecServingClient(
            @Value("${recommendation.serving.base-url}") String baseUrl,
            @Value("${recommendation.serving.connect-timeout-ms}") int connectTimeoutMs,
            @Value("${recommendation.serving.read-timeout-ms}") int readTimeoutMs,
            @Value("${recommendation.serving.max-attempts}") int maxAttempts,
            @Value("${recommendation.serving.failure-threshold}") int failureThreshold,
            @Value("${recommendation.serving.open-duration-ms}") long openDurationMs,
            ObjectMapper objectMapper,
            MeterRegistry meterRegistry
    ) {
        this.baseUrl = baseUrl;
        this.readTimeoutMs = readTimeoutMs;
        this.maxAttempts = maxAttempts;
        this.failureThreshold = failureThreshold;
        this.openDurationMs = openDurationMs;
        this.objectMapper = objectMapper;
        this.meterRegistry = meterRegistry;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(connectTimeoutMs))
                .build();
    }

    public RecommendationResult recommend(String userId, int size) {
        if (isCircuitOpen()) {
            meterRegistry.counter(
                    "rec_serving_requests_total",
                    "result",
                    "circuit_open"
            ).increment();
            throw new RecServingUnavailableException("recommendation service circuit is open");
        }

        Exception lastException = null;
        long start = System.nanoTime();
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                RecommendationResult result = doRecommend(userId, size);
                consecutiveFailures.set(0);
                openUntilEpochMs.set(0);
                meterRegistry.counter(
                        "rec_serving_requests_total",
                        "result",
                        "success"
                ).increment();
                meterRegistry.timer("rec_serving_latency").record(
                        Duration.ofNanos(System.nanoTime() - start)
                );
                return result;
            } catch (Exception exception) {
                lastException = exception;
            }
        }

        recordFailure();
        meterRegistry.counter(
                "rec_serving_requests_total",
                "result",
                "failure"
        ).increment();
        throw new RecServingUnavailableException(
                "recommendation service unavailable after " + maxAttempts + " attempts",
                lastException
        );
    }

    public boolean isHealthy() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/health"))
                    .timeout(Duration.ofMillis(readTimeoutMs))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(
                    request,
                    HttpResponse.BodyHandlers.ofString()
            );
            return response.statusCode() == 200;
        } catch (Exception ignored) {
            return false;
        }
    }

    private RecommendationResult doRecommend(String userId, int size) throws Exception {
        String body = objectMapper.writeValueAsString(new RecommendRequest(userId, size));
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/v1/recommend"))
                .timeout(Duration.ofMillis(readTimeoutMs))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        HttpResponse<String> response = httpClient.send(
                request,
                HttpResponse.BodyHandlers.ofString()
        );
        if (response.statusCode() != 200) {
            throw new IllegalStateException("recommendation service status " + response.statusCode());
        }

        JsonNode root = objectMapper.readTree(response.body());
        String requestId = root.path("request_id").asText(null);
        List<Long> itemIds = new ArrayList<>();
        for (JsonNode item : root.path("items")) {
            itemIds.add(item.path("item_id").asLong());
        }
        return new RecommendationResult(requestId, itemIds);
    }

    private boolean isCircuitOpen() {
        long openUntil = openUntilEpochMs.get();
        if (openUntil == 0) {
            return false;
        }
        if (System.currentTimeMillis() < openUntil) {
            return true;
        }
        synchronized (this) {
            if (System.currentTimeMillis() >= openUntilEpochMs.get()) {
                openUntilEpochMs.set(0);
                consecutiveFailures.set(0);
            }
        }
        return false;
    }

    private void recordFailure() {
        int failures = consecutiveFailures.incrementAndGet();
        if (failures >= failureThreshold) {
            openUntilEpochMs.set(System.currentTimeMillis() + openDurationMs);
        }
    }

    public record RecommendationResult(String requestId, List<Long> itemIds) {
    }

    private record RecommendRequest(String user_id, int size) {
    }
}
