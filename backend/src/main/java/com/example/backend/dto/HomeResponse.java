package com.example.backend.dto;

import java.util.List;

public record HomeResponse(
        String requestId,
        String recommendationId,
        String userId,
        List<ItemResponse> items
) {
}
