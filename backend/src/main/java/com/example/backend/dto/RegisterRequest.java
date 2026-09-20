package com.example.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank(message = "不能为空")
        @Size(min = 3, max = 64, message = "长度应为3到64")
        String username,

        @NotBlank(message = "不能为空")
        @Size(min = 6, max = 64, message = "长度应为6到64")
        String password
) {
}
