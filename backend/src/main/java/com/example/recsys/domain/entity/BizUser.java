package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("biz_user")
public class BizUser {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String userId;
    private String username;
    private String passwordHash;
    private String nickname;
    private String avatarUrl;
    private String phone;
    private String email;
    private Integer gender;
    private String ageLevel;
    private String defaultGeohash;
    private Integer userType;
    private Integer status;
    private LocalDateTime lastLoginAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getUsername() { return username; } public void setUsername(String v) { username = v; }
    public String getPasswordHash() { return passwordHash; } public void setPasswordHash(String v) { passwordHash = v; }
    public String getNickname() { return nickname; } public void setNickname(String v) { nickname = v; }
    public String getAvatarUrl() { return avatarUrl; } public void setAvatarUrl(String v) { avatarUrl = v; }
    public String getPhone() { return phone; } public void setPhone(String v) { phone = v; }
    public String getEmail() { return email; } public void setEmail(String v) { email = v; }
    public Integer getGender() { return gender; } public void setGender(Integer v) { gender = v; }
    public String getAgeLevel() { return ageLevel; } public void setAgeLevel(String v) { ageLevel = v; }
    public String getDefaultGeohash() { return defaultGeohash; } public void setDefaultGeohash(String v) { defaultGeohash = v; }
    public Integer getUserType() { return userType; } public void setUserType(Integer v) { userType = v; }
    public Integer getStatus() { return status; } public void setStatus(Integer v) { status = v; }
    public LocalDateTime getLastLoginAt() { return lastLoginAt; } public void setLastLoginAt(LocalDateTime v) { lastLoginAt = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
    public LocalDateTime getUpdatedAt() { return updatedAt; } public void setUpdatedAt(LocalDateTime v) { updatedAt = v; }
}
