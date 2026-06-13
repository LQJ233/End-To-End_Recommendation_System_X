package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@TableName("biz_item")
public class BizItem {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String itemId;
    private String title;
    private String itemCategory;
    private String itemGeohash;
    private String brand;
    private String styleTags;
    private String priceBucket;
    private BigDecimal price;
    private String imageUrl;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getItemId() { return itemId; } public void setItemId(String v) { itemId = v; }
    public String getTitle() { return title; } public void setTitle(String v) { title = v; }
    public String getItemCategory() { return itemCategory; } public void setItemCategory(String v) { itemCategory = v; }
    public String getItemGeohash() { return itemGeohash; } public void setItemGeohash(String v) { itemGeohash = v; }
    public String getBrand() { return brand; } public void setBrand(String v) { brand = v; }
    public String getStyleTags() { return styleTags; } public void setStyleTags(String v) { styleTags = v; }
    public String getPriceBucket() { return priceBucket; } public void setPriceBucket(String v) { priceBucket = v; }
    public BigDecimal getPrice() { return price; } public void setPrice(BigDecimal v) { price = v; }
    public String getImageUrl() { return imageUrl; } public void setImageUrl(String v) { imageUrl = v; }
    public Integer getStatus() { return status; } public void setStatus(Integer v) { status = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
    public LocalDateTime getUpdatedAt() { return updatedAt; } public void setUpdatedAt(LocalDateTime v) { updatedAt = v; }
}
