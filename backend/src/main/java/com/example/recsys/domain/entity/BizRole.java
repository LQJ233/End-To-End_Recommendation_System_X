package com.example.recsys.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import java.time.LocalDateTime;

@TableName("biz_role")
public class BizRole {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String roleCode;
    private String roleName;
    private LocalDateTime createdAt;

    public Long getId() { return id; } public void setId(Long v) { id = v; }
    public String getRoleCode() { return roleCode; } public void setRoleCode(String v) { roleCode = v; }
    public String getRoleName() { return roleName; } public void setRoleName(String v) { roleName = v; }
    public LocalDateTime getCreatedAt() { return createdAt; } public void setCreatedAt(LocalDateTime v) { createdAt = v; }
}
