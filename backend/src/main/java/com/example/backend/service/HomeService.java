package com.example.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.backend.dto.HomeResponse;
import com.example.backend.dto.ItemResponse;
import com.example.backend.entity.Item;
import com.example.backend.entity.RecommendationLog;
import com.example.backend.mapper.ItemMapper;
import com.example.backend.mapper.RecommendationLogMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class HomeService {

    private static final Logger log = LoggerFactory.getLogger(HomeService.class);
    private static final int HOME_SIZE = 20;

    private final ItemMapper itemMapper;
    private final RedisCacheService redisCacheService;
    private final ObjectMapper objectMapper;
    private final RecServingClient recServingClient;
    private final RecommendationLogMapper recommendationLogMapper;

    public HomeService(
            ItemMapper itemMapper,
            RedisCacheService redisCacheService,
            ObjectMapper objectMapper,
            RecServingClient recServingClient,
            RecommendationLogMapper recommendationLogMapper
    ) {
        this.itemMapper = itemMapper;
        this.redisCacheService = redisCacheService;
        this.objectMapper = objectMapper;
        this.recServingClient = recServingClient;
        this.recommendationLogMapper = recommendationLogMapper;
    }

    public HomeResponse getHome(String userId) {
        String cacheKey = "adrec:home:" + userId;
        String cached = redisCacheService.get(cacheKey);
        if (cached != null) {
            try {
                return objectMapper.readValue(cached, HomeResponse.class);
            } catch (JsonProcessingException ignored) {
                // 缓存内容异常时重新构建
            }
        }

        String requestId = "req-" + UUID.randomUUID();
        List<ItemResponse> itemResponses = List.of();
        try {
            RecServingClient.RecommendationResult recommendation =
                    recServingClient.recommend(userId, HOME_SIZE);
            if (recommendation.requestId() != null && !recommendation.requestId().isBlank()) {
                requestId = recommendation.requestId();
            }
            itemResponses = loadItemsInRecommendationOrder(recommendation.itemIds());
        } catch (RecServingUnavailableException exception) {
            log.warn("Recommendation service unavailable, using fallback list: {}", exception.getMessage());
        }

        if (itemResponses.isEmpty()) {
            itemResponses = loadDefaultItems();
        } else {
            itemResponses = fillToHomeSize(itemResponses);
        }

        String recommendationId = "rec-" + UUID.randomUUID();
        HomeResponse response = new HomeResponse(requestId, recommendationId, userId, itemResponses);
        saveRecommendationLog(userId, requestId, recommendationId, itemResponses);

        try {
            redisCacheService.set(
                    cacheKey,
                    objectMapper.writeValueAsString(response),
                    Duration.ofSeconds(30)
            );
        } catch (JsonProcessingException ignored) {
            // 缓存写入失败不影响响应
        }
        return response;
    }

    private List<ItemResponse> loadItemsInRecommendationOrder(List<Long> itemIds) {
        if (itemIds == null || itemIds.isEmpty()) {
            return List.of();
        }
        List<Item> items = itemMapper.selectBatchIds(itemIds);
        Map<Long, Item> itemById = items.stream()
                .collect(Collectors.toMap(Item::getId, Function.identity()));
        return itemIds.stream()
                .map(itemById::get)
                .filter(Objects::nonNull)
                .map(ItemResponse::from)
                .toList();
    }

    private List<ItemResponse> loadDefaultItems() {
        return itemMapper.selectList(new LambdaQueryWrapper<Item>()
                        .eq(Item::getStatus, 1)
                        .orderByAsc(Item::getId)
                        .last("LIMIT " + HOME_SIZE))
                .stream()
                .map(ItemResponse::from)
                .toList();
    }

    private List<ItemResponse> fillToHomeSize(List<ItemResponse> currentItems) {
        LinkedHashSet<Long> itemIds = currentItems.stream()
                .map(ItemResponse::id)
                .collect(Collectors.toCollection(LinkedHashSet::new));
        List<ItemResponse> result = new ArrayList<>(currentItems);
        for (ItemResponse fallbackItem : loadDefaultItems()) {
            if (result.size() >= HOME_SIZE) {
                break;
            }
            if (itemIds.add(fallbackItem.id())) {
                result.add(fallbackItem);
            }
        }
        return result;
    }

    private void saveRecommendationLog(
            String userId,
            String requestId,
            String recommendationId,
            List<ItemResponse> items
    ) {
        try {
            RecommendationLog recommendationLog = new RecommendationLog();
            recommendationLog.setRequestId(requestId);
            recommendationLog.setRecommendationId(recommendationId);
            recommendationLog.setUserId(userId);
            recommendationLog.setScene("home");
            recommendationLog.setItemIds(objectMapper.writeValueAsString(
                    items.stream().map(ItemResponse::id).toList()
            ));
            recommendationLogMapper.insert(recommendationLog);
        } catch (Exception exception) {
            log.warn("Failed to save recommendation log: {}", exception.getMessage());
        }
    }
}
