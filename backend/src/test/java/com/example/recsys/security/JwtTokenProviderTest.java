package com.example.recsys.security;

import com.example.recsys.common.config.AppProperties;
import io.jsonwebtoken.Claims;
import org.junit.jupiter.api.Test;
import org.springframework.mock.env.MockEnvironment;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 纯单元测试: 不启动 Spring, 直接 new JwtTokenProvider + AppProperties.
 */
class JwtTokenProviderTest {

    private AppProperties propsWithSecret(String secret, int expireMin) {
        AppProperties p = new AppProperties();
        p.getAuth().setJwtSecret(secret);
        p.getAuth().setAccessTokenExpireMinutes(expireMin);
        return p;
    }

    @Test
    void issuesAndParsesToken() {
        AppProperties p = propsWithSecret("this_is_a_test_secret_that_is_long_enough_32+", 60);
        JwtTokenProvider provider = new JwtTokenProvider(p, new MockEnvironment().withProperty("spring.profiles.active", "local"));

        String token = provider.issue("u_1", "alice", List.of("USER", "ADMIN"));
        assertNotNull(token);

        Claims claims = provider.parse(token);
        assertEquals("u_1", claims.getSubject());
        assertEquals("alice", claims.get("username"));
        assertEquals(List.of("USER", "ADMIN"), claims.get("roles", List.class));
    }

    @Test
    void rejectsDefaultSecretInNonLocalProfile() {
        AppProperties p = propsWithSecret("xx_change_me_xx_change_me_xx_change_me", 60);
        MockEnvironment env = new MockEnvironment();
        env.setActiveProfiles("prod");

        assertThrows(IllegalStateException.class, () -> new JwtTokenProvider(p, env));
    }

    @Test
    void allowsDefaultSecretInLocalProfile() {
        AppProperties p = propsWithSecret("xx_change_me_xx_change_me_xx_change_me", 60);
        MockEnvironment env = new MockEnvironment();
        env.setActiveProfiles("local");

        assertDoesNotThrow(() -> new JwtTokenProvider(p, env));
    }
}
