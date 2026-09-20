package com.example.backend.integration;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION_TESTS", matches = "true")
class BackendIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void registerHomeItemAndTrackingFlowWorks() {
        String suffix = String.valueOf(System.currentTimeMillis());
        String username = "integration_" + suffix;
        String baseUrl = "http://127.0.0.1:" + port;

        ResponseEntity<Map> register = restTemplate.postForEntity(
                baseUrl + "/api/v1/auth/register",
                Map.of("username", username, "password", "password123"),
                Map.class
        );
        assertThat(register.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(register.getBody()).isNotNull();
        assertThat(register.getBody().get("code")).isEqualTo(0);
        Map<String, Object> registerData = (Map<String, Object>) register.getBody().get("data");
        assertThat(registerData.get("token")).asString().isNotBlank();

        HttpHeaders headers = new HttpHeaders();
        headers.set("X-User-Id", username);
        ResponseEntity<String> home = restTemplate.exchange(
                baseUrl + "/api/v1/home",
                HttpMethod.GET,
                new HttpEntity<>(headers),
                String.class
        );
        assertThat(home.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(home.getBody()).contains("\"code\":0");
        assertThat(home.getBody()).contains("\"items\"");

        ResponseEntity<String> item = restTemplate.getForEntity(baseUrl + "/api/v1/items/1", String.class);
        assertThat(item.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(item.getBody()).contains("\"id\":1");

        Map<String, Object> event = Map.of(
                "eventId", "evt-integration-" + suffix,
                "userId", username,
                "sessionId", "session-integration-" + suffix,
                "itemId", 1,
                "eventType", "expose",
                "page", "home",
                "position", 1,
                "source", "card_exposure",
                "eventTime", System.currentTimeMillis()
        );
        ResponseEntity<String> eventResponse = restTemplate.postForEntity(
                baseUrl + "/api/v1/events",
                event,
                String.class
        );
        assertThat(eventResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(eventResponse.getBody()).contains("\"code\":0");
    }

    @Test
    void corsAllowsFrontendOrigin() {
        String baseUrl = "http://127.0.0.1:" + port;
        HttpHeaders headers = new HttpHeaders();
        headers.setOrigin("http://127.0.0.1:5173");
        headers.setAccessControlRequestMethod(HttpMethod.POST);

        ResponseEntity<String> response = restTemplate.exchange(
                baseUrl + "/api/v1/events",
                HttpMethod.OPTIONS,
                new HttpEntity<>(headers),
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getHeaders().getAccessControlAllowOrigin())
                .isEqualTo("http://127.0.0.1:5173");
    }
}
