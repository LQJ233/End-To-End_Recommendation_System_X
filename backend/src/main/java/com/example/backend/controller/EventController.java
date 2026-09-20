package com.example.backend.controller;

import com.example.backend.common.ApiResponse;
import com.example.backend.dto.EventReportRequest;
import com.example.backend.service.EventService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class EventController {

    private final EventService eventService;

    public EventController(EventService eventService) {
        this.eventService = eventService;
    }

    @PostMapping("/events")
    public ApiResponse<Void> report(@Valid @RequestBody EventReportRequest request) {
        eventService.report(request);
        return ApiResponse.success();
    }
}
