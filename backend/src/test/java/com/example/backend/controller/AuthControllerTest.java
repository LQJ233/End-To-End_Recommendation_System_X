package com.example.backend.controller;

import com.example.backend.dto.AuthResponse;
import com.example.backend.dto.LoginRequest;
import com.example.backend.dto.RegisterRequest;
import com.example.backend.service.AuthService;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class AuthControllerTest extends ControllerTestSupport {

    @Test
    void registerReturnsUnifiedResponse() throws Exception {
        AuthService authService = org.mockito.Mockito.mock(AuthService.class);
        when(authService.register(any(RegisterRequest.class)))
                .thenReturn(new AuthResponse(1L, "alice", "token-1"));
        MockMvc mvc = mockMvc(new AuthController(authService));

        mvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"username":"alice","password":"password123"}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data.userId").value(1))
                .andExpect(jsonPath("$.data.token").value("token-1"));
    }

    @Test
    void loginReturnsUnifiedResponse() throws Exception {
        AuthService authService = org.mockito.Mockito.mock(AuthService.class);
        when(authService.login(any(LoginRequest.class)))
                .thenReturn(new AuthResponse(2L, "bob", "token-2"));
        MockMvc mvc = mockMvc(new AuthController(authService));

        mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"username":"bob","password":"password123"}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.username").value("bob"));
    }
}
