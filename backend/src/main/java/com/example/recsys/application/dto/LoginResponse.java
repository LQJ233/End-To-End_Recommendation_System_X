package com.example.recsys.application.dto;

import java.util.List;

public class LoginResponse {
    private String accessToken;
    private String refreshToken;
    private String tokenType = "Bearer";
    private long expiresIn;
    private long refreshExpiresIn;
    private UserDto user;

    public static class UserDto {
        private String userId;
        private String username;
        private String nickname;
        private List<String> roles;
        public UserDto(String userId, String username, String nickname, List<String> roles) {
            this.userId = userId; this.username = username; this.nickname = nickname; this.roles = roles;
        }
        public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
        public String getUsername() { return username; } public void setUsername(String v) { username = v; }
        public String getNickname() { return nickname; } public void setNickname(String v) { nickname = v; }
        public List<String> getRoles() { return roles; } public void setRoles(List<String> v) { roles = v; }
    }

    public String getAccessToken() { return accessToken; } public void setAccessToken(String v) { accessToken = v; }
    public String getRefreshToken() { return refreshToken; } public void setRefreshToken(String v) { refreshToken = v; }
    public String getTokenType() { return tokenType; } public void setTokenType(String v) { tokenType = v; }
    public long getExpiresIn() { return expiresIn; } public void setExpiresIn(long v) { expiresIn = v; }
    public long getRefreshExpiresIn() { return refreshExpiresIn; } public void setRefreshExpiresIn(long v) { refreshExpiresIn = v; }
    public UserDto getUser() { return user; } public void setUser(UserDto v) { user = v; }
}
