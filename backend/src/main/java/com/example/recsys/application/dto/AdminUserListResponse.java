package com.example.recsys.application.dto;

import java.time.LocalDateTime;
import java.util.List;

public class AdminUserListResponse {
    private long total;
    private List<Record> records;
    public AdminUserListResponse(long total, List<Record> records) {
        this.total = total; this.records = records;
    }
    public long getTotal() { return total; } public void setTotal(long v) { total = v; }
    public List<Record> getRecords() { return records; } public void setRecords(List<Record> v) { records = v; }

    public static class Record {
        private String userId;
        private String username;
        private String nickname;
        private String phone;
        private Integer status;
        private List<String> roles;
        private LocalDateTime createdAt;
        public Record(String userId, String username, String nickname, String phone, Integer status,
                      List<String> roles, LocalDateTime createdAt) {
            this.userId = userId; this.username = username; this.nickname = nickname;
            this.phone = phone; this.status = status; this.roles = roles; this.createdAt = createdAt;
        }
        public String getUserId() { return userId; } public String getUsername() { return username; }
        public String getNickname() { return nickname; } public String getPhone() { return phone; }
        public Integer getStatus() { return status; } public List<String> getRoles() { return roles; }
        public LocalDateTime getCreatedAt() { return createdAt; }
    }
}
