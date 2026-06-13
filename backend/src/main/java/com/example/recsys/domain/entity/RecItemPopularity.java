package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("rec_item_popularity")
public class RecItemPopularity {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String itemId;
    private Long exposureCnt7d;
    private Long clickCnt7d;
    private Long cartCnt7d;
    private Long purchaseCnt7d;
    private Double score;
    private LocalDateTime statTime;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getItemId() { return itemId; } public void setItemId(String v) { itemId = v; }
    public Long getExposureCnt7d() { return exposureCnt7d; } public void setExposureCnt7d(Long v) { exposureCnt7d = v; }
    public Long getClickCnt7d() { return clickCnt7d; } public void setClickCnt7d(Long v) { clickCnt7d = v; }
    public Long getCartCnt7d() { return cartCnt7d; } public void setCartCnt7d(Long v) { cartCnt7d = v; }
    public Long getPurchaseCnt7d() { return purchaseCnt7d; } public void setPurchaseCnt7d(Long v) { purchaseCnt7d = v; }
    public Double getScore() { return score; } public void setScore(Double v) { score = v; }
    public LocalDateTime getStatTime() { return statTime; } public void setStatTime(LocalDateTime v) { statTime = v; }
}
