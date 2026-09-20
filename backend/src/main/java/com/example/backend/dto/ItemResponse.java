package com.example.backend.dto;

import com.example.backend.entity.Item;

import java.math.BigDecimal;

public record ItemResponse(
        Long id,
        String title,
        Long categoryId,
        Long brandId,
        BigDecimal price,
        String imageUrl,
        Integer status
) {
    public static ItemResponse from(Item item) {
        return new ItemResponse(
                item.getId(),
                item.getTitle(),
                item.getCategoryId(),
                item.getBrandId(),
                item.getPrice(),
                item.getImageUrl(),
                item.getStatus()
        );
    }
}
