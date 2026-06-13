package com.example.recsys.application.dto;

public class UpdateProfileRequest {
    private String nickname;
    private String avatarUrl;
    private String phone;
    private String email;
    private Integer gender;
    private String ageLevel;
    private String defaultGeohash;
    public String getNickname() { return nickname; } public void setNickname(String v) { nickname = v; }
    public String getAvatarUrl() { return avatarUrl; } public void setAvatarUrl(String v) { avatarUrl = v; }
    public String getPhone() { return phone; } public void setPhone(String v) { phone = v; }
    public String getEmail() { return email; } public void setEmail(String v) { email = v; }
    public Integer getGender() { return gender; } public void setGender(Integer v) { gender = v; }
    public String getAgeLevel() { return ageLevel; } public void setAgeLevel(String v) { ageLevel = v; }
    public String getDefaultGeohash() { return defaultGeohash; } public void setDefaultGeohash(String v) { defaultGeohash = v; }
}
