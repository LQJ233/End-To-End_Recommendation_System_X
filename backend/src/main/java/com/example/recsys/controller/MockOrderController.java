package com.example.recsys.controller;

import com.example.recsys.application.dto.MockOrderRequest;
import com.example.recsys.common.response.ApiResponse;
import com.example.recsys.common.util.RequestIdGenerator;
import com.example.recsys.domain.entity.BizOrderMock;
import com.example.recsys.infrastructure.mysql.BizOrderMockMapper;
import com.example.recsys.security.SecurityUtils;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/orders")
public class MockOrderController {

    private final BizOrderMockMapper mapper;

    public MockOrderController(BizOrderMockMapper mapper) {
        this.mapper = mapper;
    }

    @PostMapping("/mock")
    public ApiResponse<Map<String, String>> mock(@RequestBody MockOrderRequest req) {
        String uid = SecurityUtils.currentUserId().orElse(req.getUserId());
        if (uid == null || uid.isBlank() || req.getItemId() == null) {
            return ApiResponse.error(400001, "missing_parameter");
        }
        String orderId = "mock_order_" + RequestIdGenerator.next().substring(4);
        BizOrderMock o = new BizOrderMock();
        o.setOrderId(orderId);
        o.setUserId(uid);
        o.setItemId(req.getItemId());
        o.setAmount(BigDecimal.ZERO);
        mapper.insert(o);
        return ApiResponse.ok(Map.of("orderId", orderId));
    }
}
