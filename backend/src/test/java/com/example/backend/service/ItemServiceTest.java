package com.example.backend.service;

import com.example.backend.common.BusinessException;
import com.example.backend.common.ErrorCode;
import com.example.backend.dto.ItemResponse;
import com.example.backend.entity.Item;
import com.example.backend.mapper.ItemMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ItemServiceTest {

    @Mock
    private ItemMapper itemMapper;

    @InjectMocks
    private ItemService itemService;

    @Test
    void getItemMapsEntityToResponse() {
        Item item = new Item();
        item.setId(1001L);
        item.setTitle("广告商品 1001");
        item.setCategoryId(6406L);
        item.setBrandId(95471L);
        item.setPrice(new BigDecimal("170.00"));
        item.setStatus(1);
        when(itemMapper.selectById(1001L)).thenReturn(item);

        ItemResponse response = itemService.getItem(1001L);

        assertThat(response.id()).isEqualTo(1001L);
        assertThat(response.title()).isEqualTo("广告商品 1001");
        assertThat(response.categoryId()).isEqualTo(6406L);
        assertThat(response.brandId()).isEqualTo(95471L);
        assertThat(response.price()).isEqualByComparingTo("170.00");
    }

    @Test
    void getItemRejectsMissingItem() {
        when(itemMapper.selectById(999L)).thenReturn(null);

        assertThatThrownBy(() -> itemService.getItem(999L))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.ITEM_NOT_FOUND);
    }
}
