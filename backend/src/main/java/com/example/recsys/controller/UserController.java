package com.example.recsys.controller;

import com.example.recsys.application.AuthService;
import com.example.recsys.application.UserService;
import com.example.recsys.application.dto.ChangePasswordRequest;
import com.example.recsys.application.dto.UpdateProfileRequest;
import com.example.recsys.application.dto.UserProfileDto;
import com.example.recsys.common.response.ApiResponse;
import com.example.recsys.security.AuthUserPrincipal;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;
    private final AuthService authService;

    public UserController(UserService userService, AuthService authService) {
        this.userService = userService; this.authService = authService;
    }

    @GetMapping("/me")
    public ApiResponse<UserProfileDto> me() {
        AuthUserPrincipal p = authService.requirePrincipal();
        return ApiResponse.ok(userService.profile(p.getUserId()));
    }

    @PutMapping("/me")
    public ApiResponse<Boolean> updateMe(@RequestBody UpdateProfileRequest req) {
        AuthUserPrincipal p = authService.requirePrincipal();
        userService.updateProfile(p.getUserId(), req);
        return ApiResponse.ok(true);
    }

    @PutMapping("/me/password")
    public ApiResponse<Boolean> changePassword(@RequestBody @Valid ChangePasswordRequest req) {
        AuthUserPrincipal p = authService.requirePrincipal();
        userService.changePassword(p.getUserId(), req);
        return ApiResponse.ok(true);
    }
}
