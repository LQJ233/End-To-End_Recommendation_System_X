package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("rec_request_snapshot")
public class RecRequestSnapshot {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String requestId;
    private String userId;
    private String scene;
    private String triggerType;
    private String itemIdsJson;
    private String modelVersion;
    private LocalDateTime createdAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getRequestId() { return requestId; } public void setRequestId(String v) { requestId = v; }
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getScene() { return scene; } public void setScene(String v) { scene = v; }
    public String getTriggerType() { return triggerType; } public void setTriggerType(String v) { triggerType = v; }
    public String getItemIdsJson() { return itemIdsJson; } public void setItemIdsJson(String v) { itemIdsJson = v; }
    public String getModelVersion() { return modelVersion; } public void setModelVersion(String v) { modelVersion = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
}
