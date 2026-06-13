package com.example.recsys.controller;

import com.example.recsys.application.AuthService;
import com.example.recsys.application.dto.LoginResponse;
import com.example.recsys.application.dto.RegisterRequest;
import com.example.recsys.common.exception.BusinessException;
import com.example.recsys.common.exception.GlobalExceptionHandler;
import com.example.recsys.common.response.ErrorCode;
import com.example.recsys.domain.entity.BizUser;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;

import static org.hamcrest.Matchers.is;
import static org.mockito.ArgumentMatchers.any;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Web slice test - 不启动完整 Spring, 直接用 MockMvc + 手动注入 mock AuthService.
 * 验证 GlobalExceptionHandler 的 HTTP status / body code 映射符合 docs/05 §1.2.
 */
class AuthControllerTest {

    private AuthService authService;
    private MockMvc mvc;
    private final ObjectMapper json = new ObjectMapper();

    @BeforeEach
    void setUp() {
        authService = Mockito.mock(AuthService.class);
        AuthController controller = new AuthController(authService);
        mvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void registerSuccess() throws Exception {
        BizUser u = new BizUser();
        u.setUserId("u_1"); u.setUsername("alice"); u.setNickname("Alice");
        Mockito.when(authService.register(any())).thenReturn(u);

        mvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json.writeValueAsString(reg("alice", "Password123"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code", is(0)))
                .andExpect(jsonPath("$.data.userId", is("u_1")));
    }

    @Test
    void registerDuplicateUsername_returns409_andCorrectCode() throws Exception {
        Mockito.when(authService.register(any())).thenThrow(
                new DuplicateKeyException("Duplicate entry 'alice' for key 'uk_biz_user_username'"));

        mvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json.writeValueAsString(reg("alice", "Password123"))))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code", is(ErrorCode.USERNAME_EXISTS)))
                .andExpect(jsonPath("$.message", is("username_exists")));
    }

    @Test
    void loginAccountLocked_returns423() throws Exception {
        Mockito.when(authService.login(any(), any(HttpServletRequest.class)))
                .thenThrow(new BusinessException(ErrorCode.USER_DISABLED, "account_locked"));

        mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"a\",\"password\":\"Password123\"}"))
                .andExpect(status().isLocked())   // HTTP 423
                .andExpect(jsonPath("$.code", is(ErrorCode.USER_DISABLED)))
                .andExpect(jsonPath("$.message", is("account_locked")));
    }

    @Test
    void loginTooManyAttempts_returns429() throws Exception {
        Mockito.when(authService.login(any(), any(HttpServletRequest.class)))
                .thenThrow(new BusinessException(ErrorCode.TOO_MANY_REQUESTS, "too_many_login_attempts"));

        mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"a\",\"password\":\"Password123\"}"))
                .andExpect(status().isTooManyRequests())
                .andExpect(jsonPath("$.code", is(ErrorCode.TOO_MANY_REQUESTS)));
    }

    @Test
    void loginBadCredentials_returns401() throws Exception {
        Mockito.when(authService.login(any(), any(HttpServletRequest.class)))
                .thenThrow(new BusinessException(ErrorCode.UNAUTHORIZED, "invalid_credentials"));

        mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"a\",\"password\":\"x\"}"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code", is(ErrorCode.UNAUTHORIZED)));
    }

    @Test
    void loginSuccess() throws Exception {
        LoginResponse resp = new LoginResponse();
        resp.setAccessToken("jwt-token-here");
        resp.setExpiresIn(7200);
        resp.setUser(new LoginResponse.UserDto("u_1", "alice", "Alice", List.of("USER")));
        Mockito.when(authService.login(any(), any(HttpServletRequest.class))).thenReturn(resp);

        mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"alice\",\"password\":\"Password123\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code", is(0)))
                .andExpect(jsonPath("$.data.accessToken", is("jwt-token-here")))
                .andExpect(jsonPath("$.data.user.roles[0]", is("USER")));
    }

    private RegisterRequest reg(String u, String p) {
        RegisterRequest r = new RegisterRequest();
        r.setUsername(u); r.setPassword(p);
        return r;
    }
}
