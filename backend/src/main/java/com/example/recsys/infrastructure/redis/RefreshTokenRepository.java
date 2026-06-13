package com.example.recsys.infrastructure.redis;

import com.example.recsys.common.config.AppProperties;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

import java.security.SecureRandom;
import java.time.Duration;
import java.util.Base64;
import java.util.Map;
import java.util.Optional;

/**
 * refresh_token 存储 + 旋转.
 *
 * Redis 模型:
 *   auth:refresh:{tokenId}        -> "userId"      (TTL = refreshExpireDays)
 *   auth:refresh:user:{userId}    -> Set of tokenId (用于强制下线时批量清理)
 *
 * 使用一次性原则 (one-shot rotation): 每次 /auth/refresh 用掉一个 refresh token,
 * 立刻删除该 tokenId, 同时签发新 refresh token. 防止 token 被泄露后重复使用.
 */
@Repository
public class RefreshTokenRepository {

    private static final String TOKEN_PREFIX = "auth:refresh:";
    private static final String USER_PREFIX = "auth:refresh:user:";
    private static final SecureRandom RNG = new SecureRandom();

    private final StringRedisTemplate redis;
    private final AppProperties props;

    public RefreshTokenRepository(StringRedisTemplate redis, AppProperties props) {
        this.redis = redis;
        this.props = props;
    }

    public String issue(String userId) {
        String tokenId = randomTokenId();
        long ttlSec = Duration.ofDays(props.getAuth().getRefreshTokenExpireDays()).toSeconds();
        redis.opsForValue().set(TOKEN_PREFIX + tokenId, userId, Duration.ofSeconds(ttlSec));
        redis.opsForSet().add(USER_PREFIX + userId, tokenId);
        redis.expire(USER_PREFIX + userId, Duration.ofSeconds(ttlSec + 60));
        return tokenId;
    }

    public Optional<String> consume(String tokenId) {
        if (tokenId == null || tokenId.isBlank()) return Optional.empty();
        String key = TOKEN_PREFIX + tokenId;
        String userId = redis.opsForValue().get(key);
        if (userId == null) return Optional.empty();
        // 一次性: 立刻删除, 防止重放
        redis.delete(key);
        redis.opsForSet().remove(USER_PREFIX + userId, tokenId);
        return Optional.of(userId);
    }

    public int revokeAllForUser(String userId) {
        var set = redis.opsForSet().members(USER_PREFIX + userId);
        if (set == null || set.isEmpty()) return 0;
        int n = 0;
        for (String t : set) {
            Boolean removed = redis.delete(TOKEN_PREFIX + t);
            if (Boolean.TRUE.equals(removed)) n++;
        }
        redis.delete(USER_PREFIX + userId);
        return n;
    }

    private static String randomTokenId() {
        byte[] bytes = new byte[32];
        RNG.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
}
