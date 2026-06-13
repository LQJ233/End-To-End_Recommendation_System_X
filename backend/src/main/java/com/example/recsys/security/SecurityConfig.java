package com.example.recsys.security;

import com.example.recsys.common.config.AppProperties;
import com.example.recsys.common.response.ApiResponse;
import com.example.recsys.common.response.ErrorCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;
    private final AppProperties props;

    public SecurityConfig(JwtAuthenticationFilter jwtFilter, AppProperties props) {
        this.jwtFilter = jwtFilter; this.props = props;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(props.getAuth().getBcryptStrength());
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> {})
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(reg -> reg
                // 公开接口必须显式列出, 其他路径默认要求登录
                .requestMatchers(
                    "/api/v1/auth/**",
                    "/api/v1/items/**",
                    "/api/v1/recommendations/**",
                    "/track/**",
                    "/actuator/health/**",
                    "/actuator/info",
                    "/actuator/metrics/**",
                    "/actuator/circuitbreakers/**",
                    "/actuator/circuitbreakerevents/**",
                    "/actuator/prometheus",
                    "/static/**"
                ).permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole(props.getAuth().getAdminRole())
                .requestMatchers("/api/v1/users/**").authenticated()
                .requestMatchers("/api/v1/orders/**").authenticated()
                // 任何忘记登记的路径默认拒绝, 防止新接口裸奔
                .anyRequest().denyAll()
            )
            .exceptionHandling(e -> e
                .authenticationEntryPoint((req, resp, ex) -> writeJson(resp, 401, ErrorCode.UNAUTHORIZED, "unauthorized"))
                .accessDeniedHandler((req, resp, ex) -> writeJson(resp, 403, ErrorCode.FORBIDDEN, "forbidden"))
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    /**
     * 必须返回真实 HTTP 状态码, 否则前端 axios 拦截器无法靠 status 区分.
     * body 仍是统一的 ApiResponse JSON, 业务代码可同时使用 status 和 body.code.
     */
    private void writeJson(jakarta.servlet.http.HttpServletResponse resp, int httpStatus, int code, String msg) throws java.io.IOException {
        resp.setStatus(httpStatus);
        resp.setContentType(MediaType.APPLICATION_JSON_VALUE);
        resp.setCharacterEncoding("UTF-8");
        new ObjectMapper().writeValue(resp.getOutputStream(), ApiResponse.error(code, msg));
    }
}
