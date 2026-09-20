package com.example.backend.controller;

import com.example.backend.common.ApiResponse;
import com.example.backend.dto.HomeResponse;
import com.example.backend.service.HomeService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class HomeController {

    private final HomeService homeService;

    public HomeController(HomeService homeService) {
        this.homeService = homeService;
    }

    @GetMapping("/home")
    public ApiResponse<HomeResponse> home(@RequestHeader(value = "X-User-Id", defaultValue = "anonymous") String userId) {
        return ApiResponse.success(homeService.getHome(userId));
    }
}
