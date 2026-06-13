package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("biz_user_role")
public class BizUserRole {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String userId;
    private String roleCode;
    private LocalDateTime createdAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getUserId() { return userId; } public void setUserId(String v) { userId = v; }
    public String getRoleCode() { return roleCode; } public void setRoleCode(String v) { roleCode = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
}
