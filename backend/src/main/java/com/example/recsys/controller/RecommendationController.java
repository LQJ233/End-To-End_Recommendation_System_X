package com.example.recsys.controller;

import com.example.recsys.application.RecommendationService;
import com.example.recsys.application.dto.*;
import com.example.recsys.common.response.ApiResponse;
import com.example.recsys.security.SecurityUtils;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/recommendations")
public class RecommendationController {

    private final RecommendationService service;

    public RecommendationController(RecommendationService service) {
        this.service = service;
    }

    @GetMapping("/home")
    public ApiResponse<HomePageResponse> home(
            @RequestParam(required = false) String userId,
            @RequestParam(required = false) String scene,
            @RequestParam(defaultValue = "0") int cursor,
            @RequestParam(defaultValue = "20") int size) {
        String uid = SecurityUtils.currentUserId().orElse(userId);
        if (uid == null || uid.isBlank()) return ApiResponse.error(400001, "missing_userId");
        return ApiResponse.ok(service.page(uid, scene, cursor, size));
    }

    @PostMapping("/refresh")
    public ApiResponse<RefreshResponse> refresh(@RequestBody RefreshRequest req) {
        String uid = SecurityUtils.currentUserId().orElse(req.getUserId());
        if (uid == null || uid.isBlank()) return ApiResponse.error(400001, "missing_userId");
        req.setUserId(uid);
        RecommendationService.RefreshResult r = service.refresh(req);
        return ApiResponse.ok(r.response(), r.requestId());
    }

    @PostMapping("/exposure")
    public ApiResponse<Map<String, Object>> exposure(@RequestBody ExposureRequest req) {
        String uid = SecurityUtils.currentUserId().orElse(req.getUserId());
        if (uid == null || uid.isBlank()) return ApiResponse.error(400001, "missing_userId");
        req.setUserId(uid);
        boolean all = service.confirmExposure(req);
        return ApiResponse.ok(Map.of("allExposed", all));
    }
}
