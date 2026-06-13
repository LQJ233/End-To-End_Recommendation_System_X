package com.example.recsys.infrastructure.redis;

import com.example.recsys.common.config.AppProperties;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

import java.time.Duration;
import java.util.Collections;
import java.util.Set;

@Repository
public class AuthRedisRepository {
    private static final String BLACKLIST_PREFIX = "auth:blacklist:";
    private static final String USER_TOKENS_PREFIX = "auth:user:tokens:";

    private final StringRedisTemplate redis;
    private final AppProperties props;

    public AuthRedisRepository(StringRedisTemplate redis, AppProperties props) {
        this.redis = redis; this.props = props;
    }

    public boolean isBlacklisted(String tokenId) {
        if (!props.getAuth().isEnableTokenBlacklist()) return false;
        Boolean has = redis.hasKey(BLACKLIST_PREFIX + tokenId);
        return Boolean.TRUE.equals(has);
    }

    public void blacklist(String tokenId, long expireSeconds) {
        if (!props.getAuth().isEnableTokenBlacklist()) return;
        redis.opsForValue().set(BLACKLIST_PREFIX + tokenId, "1", Duration.ofSeconds(Math.max(60, expireSeconds)));
    }

    /**
     * 每次签发 token 时把 tokenId 加进 user 的 token 集合, 用于事后强制下线.
     * TTL 跟 token 一致即可, 过期自动清理.
     */
    public void trackUserToken(String userId, String tokenId, long expireSeconds) {
        if (!props.getAuth().isEnableTokenBlacklist()) return;
        String key = USER_TOKENS_PREFIX + userId;
        redis.opsForSet().add(key, tokenId);
        redis.expire(key, Duration.ofSeconds(Math.max(60, expireSeconds + 60)));
    }

    /**
     * 把该用户所有未过期 token 加入黑名单 (账号禁用/重置密码/角色变更时).
     */
    public int invalidateAllForUser(String userId, long blacklistTtlSec) {
        if (!props.getAuth().isEnableTokenBlacklist()) return 0;
        String key = USER_TOKENS_PREFIX + userId;
        Set<String> tokens = redis.opsForSet().members(key);
        if (tokens == null || tokens.isEmpty()) return 0;
        for (String t : tokens) {
            blacklist(t, blacklistTtlSec);
        }
        redis.delete(key);
        return tokens.size();
    }
}
