package com.example.backend.controller;

import com.example.backend.dto.ItemResponse;
import com.example.backend.service.ItemService;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class ItemControllerTest extends ControllerTestSupport {

    @Test
    void getItemReturnsItemPayload() throws Exception {
        ItemService itemService = mock(ItemService.class);
        when(itemService.getItem(1001L))
                .thenReturn(new ItemResponse(
                        1001L,
                        "广告商品 1001",
                        6406L,
                        95471L,
                        new BigDecimal("170.00"),
                        null,
                        1
                ));
        MockMvc mvc = mockMvc(new ItemController(itemService));

        mvc.perform(get("/api/v1/items/1001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.id").value(1001))
                .andExpect(jsonPath("$.data.title").value("广告商品 1001"))
                .andExpect(jsonPath("$.data.price").value(170.0));
    }
}
