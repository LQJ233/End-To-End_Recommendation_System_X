package com.example.recsys.controller;

import com.example.recsys.application.AuthService;
import com.example.recsys.application.dto.LoginRequest;
import com.example.recsys.application.dto.LoginResponse;
import com.example.recsys.application.dto.RegisterRequest;
import com.example.recsys.common.response.ApiResponse;
import com.example.recsys.domain.entity.BizUser;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ApiResponse<Map<String, Object>> register(@RequestBody @Valid RegisterRequest req) {
        BizUser u = authService.register(req);
        return ApiResponse.ok(Map.of(
                "userId", u.getUserId(),
                "username", u.getUsername(),
                "nickname", u.getNickname() == null ? "" : u.getNickname()
        ));
    }

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@RequestBody @Valid LoginRequest req, HttpServletRequest http) {
        return ApiResponse.ok(authService.login(req, http));
    }

    @PostMapping("/logout")
    public ApiResponse<Boolean> logout(HttpServletRequest http) {
        String header = http.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            authService.logout(header.substring(7));
        }
        return ApiResponse.ok(true);
    }

    @PostMapping("/refresh")
    public ApiResponse<LoginResponse> refresh(@RequestBody Map<String, String> body) {
        String refreshToken = body == null ? null : body.get("refreshToken");
        return ApiResponse.ok(authService.refresh(refreshToken));
    }
}
