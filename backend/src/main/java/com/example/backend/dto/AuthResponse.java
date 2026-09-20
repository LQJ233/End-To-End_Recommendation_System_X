package com.example.backend.dto;

public record AuthResponse(
        Long userId,
        String username,
        String token
) {
}
