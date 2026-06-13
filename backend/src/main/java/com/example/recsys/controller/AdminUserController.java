package com.example.recsys.controller;

import com.example.recsys.application.UserService;
import com.example.recsys.application.dto.AdminUserListResponse;
import com.example.recsys.common.response.ApiResponse;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin/users")
public class AdminUserController {

    private final UserService userService;

    public AdminUserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    public ApiResponse<AdminUserListResponse> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String roleCode,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ApiResponse.ok(userService.adminList(keyword, status, roleCode, page, size));
    }

    @PutMapping("/{userId}/status")
    public ApiResponse<Boolean> updateStatus(@PathVariable String userId, @RequestBody Map<String, Integer> body) {
        userService.adminSetStatus(userId, body.getOrDefault("status", 1));
        return ApiResponse.ok(true);
    }

    @PutMapping("/{userId}/password")
    public ApiResponse<Boolean> resetPassword(@PathVariable String userId, @RequestBody Map<String, String> body) {
        userService.adminResetPassword(userId, body.get("newPassword"));
        return ApiResponse.ok(true);
    }

    @PutMapping("/{userId}/roles")
    public ApiResponse<Boolean> setRoles(@PathVariable String userId, @RequestBody Map<String, List<String>> body) {
        userService.adminSetRoles(userId, body.getOrDefault("roles", List.of("USER")));
        return ApiResponse.ok(true);
    }
}
