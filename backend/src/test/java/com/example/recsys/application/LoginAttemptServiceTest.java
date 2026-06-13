package com.example.recsys.application;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;

class LoginAttemptServiceTest {

    private StringRedisTemplate redis;
    private ValueOperations<String, String> ops;
    private LoginAttemptService svc;

    @BeforeEach
    @SuppressWarnings("unchecked")
    void setUp() {
        redis = Mockito.mock(StringRedisTemplate.class);
        ops = Mockito.mock(ValueOperations.class);
        Mockito.when(redis.opsForValue()).thenReturn(ops);
        svc = new LoginAttemptService(redis);
        // 强制注入测试用阈值
        ReflectionTestUtils.setField(svc, "ipMax", 5);
        ReflectionTestUtils.setField(svc, "windowSec", 60);
        ReflectionTestUtils.setField(svc, "userMaxFail", 3);
        ReflectionTestUtils.setField(svc, "userLockSec", 60);
    }

    @Test
    void isIpBlocked_underThreshold() {
        Mockito.when(ops.get("auth:login:fail:ip:127.0.0.1")).thenReturn("4");
        assertFalse(svc.isIpBlocked("127.0.0.1"));
    }

    @Test
    void isIpBlocked_atThreshold() {
        Mockito.when(ops.get("auth:login:fail:ip:127.0.0.1")).thenReturn("5");
        assertTrue(svc.isIpBlocked("127.0.0.1"));
    }

    @Test
    void isUserLocked_atThreshold() {
        Mockito.when(ops.get("auth:login:fail:user:alice")).thenReturn("3");
        assertTrue(svc.isUserLocked("alice"));
    }

    @Test
    void recordFailureIncrementsBothKeys() {
        Mockito.when(ops.increment(anyString())).thenReturn(1L);
        svc.recordFailure("127.0.0.1", "alice");
        Mockito.verify(ops).increment("auth:login:fail:ip:127.0.0.1");
        Mockito.verify(ops).increment("auth:login:fail:user:alice");
        Mockito.verify(redis, Mockito.times(2)).expire(anyString(), any());
    }

    @Test
    void recordSuccessClearsUserFailures() {
        svc.recordSuccess("alice");
        Mockito.verify(redis).delete("auth:login:fail:user:alice");
    }
}
