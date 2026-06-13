package com.example.recsys.application.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class ChangePasswordRequest {
    @NotBlank private String oldPassword;
    @NotBlank @Size(min = 6, max = 64) private String newPassword;
    public String getOldPassword() { return oldPassword; } public void setOldPassword(String v) { oldPassword = v; }
    public String getNewPassword() { return newPassword; } public void setNewPassword(String v) { newPassword = v; }
}
