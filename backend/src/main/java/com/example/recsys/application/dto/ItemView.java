package com.example.recsys.application.dto;

import com.example.recsys.domain.entity.BizItem;

import java.math.BigDecimal;

public class ItemView {
    private String itemId;
    private String title;
    private String itemCategory;
    private BigDecimal price;
    private String imageUrl;
    private String brand;
    private String priceBucket;
    private Integer status;
    private Double rankScore;

    public static ItemView from(BizItem b) {
        ItemView v = new ItemView();
        v.itemId = b.getItemId();
        v.title = b.getTitle();
        v.itemCategory = b.getItemCategory();
        v.price = b.getPrice();
        v.imageUrl = b.getImageUrl();
        v.brand = b.getBrand();
        v.priceBucket = b.getPriceBucket();
        v.status = b.getStatus();
        return v;
    }
    public String getItemId() { return itemId; } public void setItemId(String v) { itemId = v; }
    public String getTitle() { return title; } public void setTitle(String v) { title = v; }
    public String getItemCategory() { return itemCategory; } public void setItemCategory(String v) { itemCategory = v; }
    public BigDecimal getPrice() { return price; } public void setPrice(BigDecimal v) { price = v; }
    public String getImageUrl() { return imageUrl; } public void setImageUrl(String v) { imageUrl = v; }
    public String getBrand() { return brand; } public void setBrand(String v) { brand = v; }
    public String getPriceBucket() { return priceBucket; } public void setPriceBucket(String v) { priceBucket = v; }
    public Integer getStatus() { return status; } public void setStatus(Integer v) { status = v; }
    public Double getRankScore() { return rankScore; } public void setRankScore(Double v) { rankScore = v; }
}
