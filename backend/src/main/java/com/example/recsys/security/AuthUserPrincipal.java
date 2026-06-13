package com.example.recsys.security;

import java.util.List;

public class AuthUserPrincipal {
    private final String userId;
    private final String username;
    private final List<String> roles;
    private final String tokenId;
    public AuthUserPrincipal(String userId, String username, List<String> roles, String tokenId) {
        this.userId = userId; this.username = username; this.roles = roles; this.tokenId = tokenId;
    }
    public String getUserId() { return userId; }
    public String getUsername() { return username; }
    public List<String> getRoles() { return roles; }
    public String getTokenId() { return tokenId; }
}
