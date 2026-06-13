package com.example.recsys.application.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RegisterRequest {
    @NotBlank @Size(min = 3, max = 64) private String username;
    @NotBlank @Size(min = 6, max = 64) private String password;
    private String nickname;
    private String phone;
    private String email;
    public String getUsername() { return username; } public void setUsername(String v) { username = v; }
    public String getPassword() { return password; } public void setPassword(String v) { password = v; }
    public String getNickname() { return nickname; } public void setNickname(String v) { nickname = v; }
    public String getPhone() { return phone; } public void setPhone(String v) { phone = v; }
    public String getEmail() { return email; } public void setEmail(String v) { email = v; }
}
