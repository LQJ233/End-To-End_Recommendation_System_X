package com.example.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RecServingClientTest {

    private HttpServer server;
    private RecServingClient client;
    private final AtomicInteger requests = new AtomicInteger();

    @BeforeEach
    void setUp() throws IOException {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.start();
        client = new RecServingClient(
                "http://127.0.0.1:" + server.getAddress().getPort(),
                200,
                500,
                2,
                2,
                1_000,
                new ObjectMapper(),
                new SimpleMeterRegistry()
        );
    }

    @AfterEach
    void tearDown() {
        server.stop(0);
    }

    @Test
    void recommendParsesItemIds() {
        server.createContext("/v1/recommend", exchange -> {
            requests.incrementAndGet();
            respond(
                    exchange,
                    200,
                    """
                    {"request_id":"req-1","items":[{"item_id":102},{"item_id":9285}]}
                    """
            );
        });

        RecServingClient.RecommendationResult result = client.recommend("user-1", 2);

        assertThat(result.requestId()).isEqualTo("req-1");
        assertThat(result.itemIds()).containsExactly(102L, 9285L);
        assertThat(requests.get()).isEqualTo(1);
    }

    @Test
    void recommendRetriesAfterTransientFailure() {
        server.createContext("/v1/recommend", exchange -> {
            int attempt = requests.incrementAndGet();
            if (attempt == 1) {
                respond(exchange, 500, "{\"error\":\"temporary\"}");
            } else {
                respond(exchange, 200, "{\"request_id\":\"req-2\",\"items\":[{\"item_id\":7}]}");
            }
        });

        RecServingClient.RecommendationResult result = client.recommend("user-1", 1);

        assertThat(result.itemIds()).containsExactly(7L);
        assertThat(requests.get()).isEqualTo(2);
    }

    @Test
    void circuitBreakerStopsCallingAfterFailureThreshold() {
        server.createContext("/v1/recommend", exchange -> {
            requests.incrementAndGet();
            respond(exchange, 500, "{\"error\":\"down\"}");
        });

        assertThatThrownBy(() -> client.recommend("user-1", 1))
                .isInstanceOf(RecServingUnavailableException.class);
        assertThatThrownBy(() -> client.recommend("user-1", 1))
                .isInstanceOf(RecServingUnavailableException.class);
        assertThatThrownBy(() -> client.recommend("user-1", 1))
                .isInstanceOf(RecServingUnavailableException.class);

        assertThat(requests.get()).isEqualTo(4);
    }

    private static void respond(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        exchange.getResponseBody().write(bytes);
        exchange.close();
    }
}
