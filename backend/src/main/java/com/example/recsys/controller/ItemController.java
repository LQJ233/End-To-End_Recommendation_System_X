package com.example.recsys.controller;

import com.example.recsys.application.RecommendationService;
import com.example.recsys.application.dto.ItemView;
import com.example.recsys.common.response.ApiResponse;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/items")
public class ItemController {

    private final RecommendationService service;

    public ItemController(RecommendationService service) {
        this.service = service;
    }

    @GetMapping("/batch")
    public ApiResponse<Map<String, List<ItemView>>> batch(@RequestParam String itemIds) {
        if (itemIds == null || itemIds.isBlank()) {
            return ApiResponse.ok(Map.of("items", List.of()));
        }
        List<String> ids = Arrays.stream(itemIds.split(","))
                .map(String::trim).filter(s -> !s.isEmpty()).toList();
        return ApiResponse.ok(Map.of("items", service.lookupItems(ids)));
    }
}
