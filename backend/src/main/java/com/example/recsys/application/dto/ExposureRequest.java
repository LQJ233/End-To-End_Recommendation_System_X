package com.example.recsys.application.dto;

import java.util.List;

public class ExposureRequest {
    private String userId;
    private String requestId;
    private List<String> itemIds;
    private Long timestamp;
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getRequestId() { return requestId; } public void setRequestId(String v) { requestId = v; }
    public List<String> getItemIds() { return itemIds; } public void setItemIds(List<String> v) { itemIds = v; }
    public Long getTimestamp() { return timestamp; } public void setTimestamp(Long v) { timestamp = v; }
}
