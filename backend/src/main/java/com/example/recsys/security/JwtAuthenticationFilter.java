package com.example.recsys.security;

import com.example.recsys.infrastructure.redis.AuthRedisRepository;
import io.jsonwebtoken.Claims;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.stream.Collectors;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider tokenProvider;
    private final AuthRedisRepository authRedis;

    public JwtAuthenticationFilter(JwtTokenProvider tokenProvider, AuthRedisRepository authRedis) {
        this.tokenProvider = tokenProvider; this.authRedis = authRedis;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse resp, FilterChain chain)
            throws ServletException, IOException {
        String header = req.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            String token = header.substring(7);
            try {
                Claims claims = tokenProvider.parse(token);
                String tokenId = claims.getId();
                if (!authRedis.isBlacklisted(tokenId)) {
                    String userId = claims.getSubject();
                    String username = claims.get("username", String.class);
                    @SuppressWarnings("unchecked")
                    List<String> roles = (List<String>) claims.get("roles", List.class);
                    if (roles == null) roles = List.of();
                    AuthUserPrincipal principal = new AuthUserPrincipal(userId, username, roles, tokenId);
                    UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                            principal, token,
                            roles.stream().map(r -> new SimpleGrantedAuthority("ROLE_" + r)).collect(Collectors.toList())
                    );
                    SecurityContextHolder.getContext().setAuthentication(auth);
                }
            } catch (Exception ignored) {
                // invalid token -> remain anonymous
            }
        }
        chain.doFilter(req, resp);
    }
}
