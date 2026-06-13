package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("rec_behavior_log")
public class RecBehaviorLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String userId;
    private String itemId;
    private Integer behaviorType;
    private Long timestamp;
    private String requestId;
    private String scene;
    private String source;
    private LocalDateTime createdAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getItemId() { return itemId; } public void setItemId(String v) { itemId = v; }
    public Integer getBehaviorType() { return behaviorType; } public void setBehaviorType(Integer v) { behaviorType = v; }
    public Long getTimestamp() { return timestamp; } public void setTimestamp(Long v) { timestamp = v; }
    public String getRequestId() { return requestId; } public void setRequestId(String v) { requestId = v; }
    public String getScene() { return scene; } public void setScene(String v) { scene = v; }
    public String getSource() { return source; } public void setSource(String v) { source = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
}
