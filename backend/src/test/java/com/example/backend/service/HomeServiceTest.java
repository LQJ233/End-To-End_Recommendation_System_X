package com.example.backend.service;

import com.example.backend.dto.HomeResponse;
import com.example.backend.entity.Item;
import com.example.backend.mapper.ItemMapper;
import com.example.backend.mapper.RecommendationLogMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class HomeServiceTest {

    @Mock
    private ItemMapper itemMapper;

    @Mock
    private RedisCacheService redisCacheService;

    @Mock
    private RecServingClient recServingClient;

    @Mock
    private RecommendationLogMapper recommendationLogMapper;

    private ObjectMapper objectMapper;
    private HomeService homeService;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        homeService = new HomeService(
                itemMapper,
                redisCacheService,
                objectMapper,
                recServingClient,
                recommendationLogMapper
        );
    }

    @Test
    void getHomeReturnsCachedResponseWithoutQueryingDatabase() throws Exception {
        HomeResponse cached = new HomeResponse("req-cached", "rec-cached", "user-1", List.of());
        when(redisCacheService.get("adrec:home:user-1"))
                .thenReturn(objectMapper.writeValueAsString(cached));

        HomeResponse response = homeService.getHome("user-1");

        assertThat(response.requestId()).isEqualTo("req-cached");
        assertThat(response.recommendationId()).isEqualTo("rec-cached");
        verify(itemMapper, never()).selectList(any());
    }

    @Test
    void getHomeBuildsAndCachesResponseOnCacheMiss() throws Exception {
        when(redisCacheService.get("adrec:home:user-2")).thenReturn(null);
        when(recServingClient.recommend("user-2", 20))
                .thenReturn(new RecServingClient.RecommendationResult(
                        "req-from-serving",
                        List.of(1001L, 1002L)
                ));
        when(itemMapper.selectBatchIds(any())).thenReturn(List.of(item(1002L), item(1001L)));

        HomeResponse response = homeService.getHome("user-2");

        assertThat(response.userId()).isEqualTo("user-2");
        assertThat(response.items()).hasSize(2);
        assertThat(response.items().get(0).id()).isEqualTo(1001L);
        assertThat(response.requestId()).isEqualTo("req-from-serving");
        assertThat(response.recommendationId()).startsWith("rec-");

        ArgumentCaptor<String> valueCaptor = ArgumentCaptor.forClass(String.class);
        verify(redisCacheService).set(anyString(), valueCaptor.capture(), any(Duration.class));
        HomeResponse cached = objectMapper.readValue(valueCaptor.getValue(), HomeResponse.class);
        assertThat(cached.requestId()).isEqualTo(response.requestId());
    }

    @Test
    void getHomeRebuildsWhenCachedJsonIsMalformed() {
        when(redisCacheService.get("adrec:home:user-3")).thenReturn("{not-json");
        when(recServingClient.recommend("user-3", 20))
                .thenThrow(new RecServingUnavailableException("rec serving down"));
        when(itemMapper.selectList(any())).thenReturn(List.of(item(1003L)));

        HomeResponse response = homeService.getHome("user-3");

        assertThat(response.items()).hasSize(1);
        assertThat(response.items().get(0).id()).isEqualTo(1003L);
        verify(redisCacheService).set(anyString(), anyString(), any(Duration.class));
    }

    @Test
    void getHomeFallsBackToDatabaseWhenRecServingReturnsEmpty() {
        when(redisCacheService.get("adrec:home:user-4")).thenReturn(null);
        when(recServingClient.recommend("user-4", 20))
                .thenReturn(new RecServingClient.RecommendationResult("req-empty", List.of()));
        when(itemMapper.selectList(any())).thenReturn(List.of(item(1004L)));

        HomeResponse response = homeService.getHome("user-4");

        assertThat(response.items()).hasSize(1);
        assertThat(response.items().get(0).id()).isEqualTo(1004L);
    }

    private static Item item(Long id) {
        Item item = new Item();
        item.setId(id);
        item.setTitle("item-" + id);
        item.setCategoryId(1L);
        item.setBrandId(2L);
        item.setPrice(new BigDecimal("9.90"));
        item.setStatus(1);
        return item;
    }
}
