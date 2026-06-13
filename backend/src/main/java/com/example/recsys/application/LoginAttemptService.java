package com.example.recsys.application;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * Redis-backed 登录失败计数 / 账号锁定.
 *
 *  - auth:login:fail:ip:{ip}        每个 IP 在 windowSec 内累计失败次数
 *  - auth:login:fail:user:{name}    每个用户名累计失败次数, 超阈值锁定 lockSec
 *
 * 锁定期间无论密码是否正确都拒绝登录, 由 AuthService 在 login() 入口判断.
 */
@Service
public class LoginAttemptService {
    private static final Logger log = LoggerFactory.getLogger(LoginAttemptService.class);

    private static final String IP_KEY = "auth:login:fail:ip:";
    private static final String USER_KEY = "auth:login:fail:user:";

    private final StringRedisTemplate redis;

    @Value("${app.auth.loginRateLimit.ipMaxPerWindow:30}")
    private int ipMax;
    @Value("${app.auth.loginRateLimit.windowSec:300}")
    private int windowSec;
    @Value("${app.auth.loginRateLimit.userMaxFailures:5}")
    private int userMaxFail;
    @Value("${app.auth.loginRateLimit.userLockSec:900}")
    private int userLockSec;

    public LoginAttemptService(StringRedisTemplate redis) {
        this.redis = redis;
    }

    public boolean isIpBlocked(String ip) {
        if (ip == null) return false;
        String v = redis.opsForValue().get(IP_KEY + ip);
        if (v == null) return false;
        try { return Integer.parseInt(v) >= ipMax; } catch (NumberFormatException e) { return false; }
    }

    public boolean isUserLocked(String username) {
        if (username == null) return false;
        String v = redis.opsForValue().get(USER_KEY + username);
        if (v == null) return false;
        try { return Integer.parseInt(v) >= userMaxFail; } catch (NumberFormatException e) { return false; }
    }

    public void recordFailure(String ip, String username) {
        incrWithTtl(IP_KEY + ip, Duration.ofSeconds(windowSec));
        incrWithTtl(USER_KEY + username, Duration.ofSeconds(userLockSec));
    }

    public void recordSuccess(String username) {
        if (username != null) redis.delete(USER_KEY + username);
    }

    private void incrWithTtl(String key, Duration ttl) {
        try {
            Long v = redis.opsForValue().increment(key);
            if (v != null && v == 1L) redis.expire(key, ttl);
        } catch (Exception e) {
            log.warn("login attempt redis op failed: {}", e.getMessage());
        }
    }
}
