package com.example.recsys.application.dto;

import java.util.List;

public class RefreshRequest {
    private String userId;
    private String scene;
    private String triggerType;
    private List<String> excludeItemIds;
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getScene() { return scene; } public void setScene(String v) { scene = v; }
    public String getTriggerType() { return triggerType; } public void setTriggerType(String v) { triggerType = v; }
    public List<String> getExcludeItemIds() { return excludeItemIds; } public void setExcludeItemIds(List<String> v) { excludeItemIds = v; }
}
