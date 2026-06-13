package com.example.recsys.security;

import com.example.recsys.common.config.AppProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Component
public class JwtTokenProvider {
    private static final Logger log = LoggerFactory.getLogger(JwtTokenProvider.class);
    private static final String DEFAULT_FRAGMENT = "change_me";

    private final AppProperties props;
    private final SecretKey key;

    public JwtTokenProvider(AppProperties props, Environment env) {
        this.props = props;
        String secret = props.getAuth().getJwtSecret();
        validateSecret(secret, env);

        byte[] bytes = secret.getBytes(StandardCharsets.UTF_8);
        if (bytes.length < 32) {
            byte[] padded = new byte[32];
            System.arraycopy(bytes, 0, padded, 0, bytes.length);
            for (int i = bytes.length; i < 32; i++) padded[i] = (byte) i;
            bytes = padded;
        }
        this.key = Keys.hmacShaKeyFor(bytes);
    }

    /**
     * 默认密钥含 "change_me" 子串时:
     *  - local profile: 仅大声警告, 方便本地启动;
     *  - 任何其他 profile (dev/staging/prod): 拒绝启动.
     */
    private static void validateSecret(String secret, Environment env) {
        boolean weak = secret == null || secret.isBlank() || secret.contains(DEFAULT_FRAGMENT);
        if (!weak) return;
        boolean localOnly = env != null
                && env.getActiveProfiles().length > 0
                && java.util.Arrays.asList(env.getActiveProfiles()).contains("local");
        if (localOnly) {
            log.warn("===========================================================");
            log.warn(" JWT secret 包含默认值 'change_me'; 仅在 local profile 启动时容忍.");
            log.warn(" 上线前必须把 app.auth.jwtSecret 改成至少 32 字节的随机串.");
            log.warn("===========================================================");
            return;
        }
        throw new IllegalStateException(
                "JWT secret 仍是默认值; 请把 conf/application-local.yml 里的 auth.jwtSecret " +
                "改成强随机串后再启动 (active profiles: " +
                String.join(",", env == null ? new String[0] : env.getActiveProfiles()) + ")");
    }

    public String issue(String userId, String username, List<String> roles) {
        long now = System.currentTimeMillis();
        long exp = now + props.getAuth().getAccessTokenExpireMinutes() * 60_000L;
        return Jwts.builder()
                .id(UUID.randomUUID().toString())
                .subject(userId)
                .claim("username", username)
                .claim("roles", roles)
                .issuedAt(new Date(now))
                .expiration(new Date(exp))
                .signWith(key)
                .compact();
    }

    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
    }

    public long expiresInSeconds() {
        return props.getAuth().getAccessTokenExpireMinutes() * 60L;
    }
}
