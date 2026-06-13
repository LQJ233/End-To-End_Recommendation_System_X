package com.example.recsys.application.dto;

import com.example.recsys.domain.entity.BizUser;

import java.util.List;

public class UserProfileDto {
    private String userId;
    private String username;
    private String nickname;
    private String avatarUrl;
    private String phone;
    private String email;
    private Integer gender;
    private String ageLevel;
    private String defaultGeohash;
    private List<String> roles;
    private Integer status;

    public static UserProfileDto from(BizUser u, List<String> roles) {
        UserProfileDto d = new UserProfileDto();
        d.userId = u.getUserId();
        d.username = u.getUsername();
        d.nickname = u.getNickname();
        d.avatarUrl = u.getAvatarUrl();
        d.phone = u.getPhone();
        d.email = u.getEmail();
        d.gender = u.getGender();
        d.ageLevel = u.getAgeLevel();
        d.defaultGeohash = u.getDefaultGeohash();
        d.status = u.getStatus();
        d.roles = roles;
        return d;
    }
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getUsername() { return username; } public void setUsername(String v) { username = v; }
    public String getNickname() { return nickname; } public void setNickname(String v) { nickname = v; }
    public String getAvatarUrl() { return avatarUrl; } public void setAvatarUrl(String v) { avatarUrl = v; }
    public String getPhone() { return phone; } public void setPhone(String v) { phone = v; }
    public String getEmail() { return email; } public void setEmail(String v) { email = v; }
    public Integer getGender() { return gender; } public void setGender(Integer v) { gender = v; }
    public String getAgeLevel() { return ageLevel; } public void setAgeLevel(String v) { ageLevel = v; }
    public String getDefaultGeohash() { return defaultGeohash; } public void setDefaultGeohash(String v) { defaultGeohash = v; }
    public List<String> getRoles() { return roles; } public void setRoles(List<String> v) { roles = v; }
    public Integer getStatus() { return status; } public void setStatus(Integer v) { status = v; }
}
