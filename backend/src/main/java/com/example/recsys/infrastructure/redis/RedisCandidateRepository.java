package com.example.recsys.infrastructure.redis;

import com.example.recsys.common.config.AppProperties;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Repository;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/** Manages rec:candidate / rec:exposed / rec:hot keys. */
@Repository
public class RedisCandidateRepository {

    /**
     * Lua: DEL + RPUSH + EXPIRE 原子执行, 防止并发刷新时新旧候选混合或 TTL 丢失.
     *   KEYS[1] = candidate key
     *   ARGV[1] = ttlSec
     *   ARGV[2..] = item ids (可能为空)
     */
    private static final DefaultRedisScript<Long> REPLACE_CANDIDATES_SCRIPT = new DefaultRedisScript<>(
            "redis.call('DEL', KEYS[1])\n" +
            "local n = #ARGV\n" +
            "if n >= 2 then\n" +
            "  for i = 2, n do\n" +
            "    redis.call('RPUSH', KEYS[1], ARGV[i])\n" +
            "  end\n" +
            "end\n" +
            "redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))\n" +
            "return 1\n",
            Long.class);

    private final StringRedisTemplate redis;
    private final AppProperties props;

    public RedisCandidateRepository(StringRedisTemplate redis, AppProperties props) {
        this.redis = redis; this.props = props;
    }

    private String candidateKey(String userId, String scene) {
        return "rec:candidate:" + userId + ":" + scene;
    }
    private String exposedKey(String userId, String requestId) {
        return "rec:exposed:" + userId + ":" + requestId;
    }
    private String cacheKey(String userId) {
        return "rec:cache:" + userId;
    }

    public void replaceCandidates(String userId, String scene, List<String> itemIds) {
        String key = candidateKey(userId, scene);
        long ttlSec = Duration.ofHours(props.getRecommendation().getCandidateTtlHours()).toSeconds();

        List<String> args = new ArrayList<>(1 + itemIds.size());
        args.add(String.valueOf(ttlSec));
        args.addAll(itemIds);
        redis.execute(REPLACE_CANDIDATES_SCRIPT, Collections.singletonList(key),
                args.toArray(new String[0]));
    }

    public long candidateSize(String userId, String scene) {
        Long n = redis.opsForList().size(candidateKey(userId, scene));
        return n == null ? 0L : n;
    }

    public List<String> readPage(String userId, String scene, int cursor, int size) {
        List<String> out = redis.opsForList().range(candidateKey(userId, scene), cursor, cursor + size - 1L);
        return out == null ? Collections.emptyList() : out;
    }

    public List<String> readAll(String userId, String scene) {
        List<String> out = redis.opsForList().range(candidateKey(userId, scene), 0, -1);
        return out == null ? Collections.emptyList() : out;
    }

    public void markExposed(String userId, String requestId, List<String> itemIds) {
        if (itemIds == null || itemIds.isEmpty()) return;
        String key = exposedKey(userId, requestId);
        redis.opsForSet().add(key, itemIds.toArray(new String[0]));
        redis.expire(key, Duration.ofHours(props.getRecommendation().getCandidateTtlHours()));
    }

    public Set<String> exposedSet(String userId, String requestId) {
        Set<String> s = redis.opsForSet().members(exposedKey(userId, requestId));
        return s == null ? Collections.emptySet() : s;
    }

    public long exposedSize(String userId, String requestId) {
        Long n = redis.opsForSet().size(exposedKey(userId, requestId));
        return n == null ? 0L : n;
    }

    public Set<String> hotItems(int n) {
        Set<String> s = redis.opsForZSet().reverseRange("rec:hot:items", 0, n - 1L);
        return s == null ? Collections.emptySet() : s;
    }

    public void removeFromCache(String userId, List<String> itemIds) {
        if (itemIds == null || itemIds.isEmpty()) return;
        redis.opsForZSet().remove(cacheKey(userId), itemIds.toArray(new String[0]));
    }
}
