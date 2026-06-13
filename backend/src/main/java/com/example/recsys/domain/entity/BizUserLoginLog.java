package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("biz_user_login_log")
public class BizUserLoginLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String userId;
    private String username;
    private String loginType;
    private String clientIp;
    private String userAgent;
    private Integer success;
    private String failReason;
    private LocalDateTime createdAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getUsername() { return username; } public void setUsername(String v) { username = v; }
    public String getLoginType() { return loginType; } public void setLoginType(String v) { loginType = v; }
    public String getClientIp() { return clientIp; } public void setClientIp(String v) { clientIp = v; }
    public String getUserAgent() { return userAgent; } public void setUserAgent(String v) { userAgent = v; }
    public Integer getSuccess() { return success; } public void setSuccess(Integer v) { success = v; }
    public String getFailReason() { return failReason; } public void setFailReason(String v) { failReason = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
}
