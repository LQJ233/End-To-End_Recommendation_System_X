package com.example.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record EventReportRequest(
        @NotBlank(message = "不能为空")
        String eventId,

        @NotBlank(message = "不能为空")
        String userId,

        @NotBlank(message = "不能为空")
        String sessionId,

        Long itemId,

        @NotBlank(message = "不能为空")
        String eventType,

        @NotBlank(message = "不能为空")
        String page,

        Integer position,

        @NotBlank(message = "不能为空")
        String source,

        String requestId,

        String recommendationId,

        @NotNull(message = "不能为空")
        Long eventTime
) {
}
