package com.example.recsys.application;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.recsys.application.dto.AdminUserListResponse;
import com.example.recsys.application.dto.ChangePasswordRequest;
import com.example.recsys.application.dto.UpdateProfileRequest;
import com.example.recsys.application.dto.UserProfileDto;
import com.example.recsys.common.exception.BusinessException;
import com.example.recsys.common.response.ErrorCode;
import com.example.recsys.domain.entity.BizUser;
import com.example.recsys.domain.entity.BizUserRole;
import com.example.recsys.infrastructure.mysql.BizUserMapper;
import com.example.recsys.infrastructure.mysql.BizUserRoleMapper;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
public class UserService {

    private final BizUserMapper userMapper;
    private final BizUserRoleMapper userRoleMapper;
    private final PasswordEncoder passwordEncoder;
    private final AuthService authService;

    public UserService(BizUserMapper userMapper, BizUserRoleMapper userRoleMapper,
                       PasswordEncoder passwordEncoder, AuthService authService) {
        this.userMapper = userMapper;
        this.userRoleMapper = userRoleMapper;
        this.passwordEncoder = passwordEncoder;
        this.authService = authService;
    }

    public BizUser findByUserId(String userId) {
        BizUser u = userMapper.selectOne(new LambdaQueryWrapper<BizUser>().eq(BizUser::getUserId, userId));
        if (u == null) throw new BusinessException(ErrorCode.UNAUTHORIZED, "user_not_found");
        return u;
    }

    public UserProfileDto profile(String userId) {
        BizUser u = findByUserId(userId);
        return UserProfileDto.from(u, authService.loadRoleCodes(userId));
    }

    public void updateProfile(String userId, UpdateProfileRequest req) {
        BizUser u = findByUserId(userId);
        if (req.getNickname() != null) u.setNickname(req.getNickname());
        if (req.getAvatarUrl() != null) u.setAvatarUrl(req.getAvatarUrl());
        if (req.getPhone() != null) u.setPhone(emptyToNull(req.getPhone()));
        if (req.getEmail() != null) u.setEmail(emptyToNull(req.getEmail()));
        if (req.getGender() != null) u.setGender(req.getGender());
        if (req.getAgeLevel() != null) u.setAgeLevel(req.getAgeLevel());
        if (req.getDefaultGeohash() != null) u.setDefaultGeohash(req.getDefaultGeohash());
        userMapper.updateById(u);
    }

    public void changePassword(String userId, ChangePasswordRequest req) {
        BizUser u = findByUserId(userId);
        if (!passwordEncoder.matches(req.getOldPassword(), u.getPasswordHash())) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "old_password_mismatch");
        }
        u.setPasswordHash(passwordEncoder.encode(req.getNewPassword()));
        userMapper.updateById(u);
        // 改密后强制该用户所有 token 失效, 不只是当前 token.
        authService.forceLogoutAll(userId);
    }

    public AdminUserListResponse adminList(String keyword, Integer status, String roleCode, int page, int size) {
        // 角色过滤直接在 SQL 里完成 (EXISTS), 保证 total 与 records 一致;
        // Java 端不再做 post-filter, 避免分页错乱.
        Page<BizUser> p = new Page<>(page, size);
        Page<BizUser> result = userMapper.selectAdminPage(p, keyword, status, roleCode);

        List<AdminUserListResponse.Record> records = new ArrayList<>(result.getRecords().size());
        for (BizUser u : result.getRecords()) {
            List<String> roles = authService.loadRoleCodes(u.getUserId());
            records.add(new AdminUserListResponse.Record(
                    u.getUserId(), u.getUsername(), u.getNickname(), u.getPhone(),
                    u.getStatus(), roles, u.getCreatedAt()));
        }
        return new AdminUserListResponse(result.getTotal(), records);
    }

    @Transactional
    public void adminSetStatus(String userId, int status) {
        BizUser u = findByUserId(userId);
        u.setStatus(status);
        userMapper.updateById(u);
        // 禁用账号: 强制下线该用户所有未过期 token (依赖 AuthService 登录时记录 token id).
        if (status == 0) {
            authService.forceLogoutAll(userId);
        }
    }

    public void adminResetPassword(String userId, String newPassword) {
        BizUser u = findByUserId(userId);
        u.setPasswordHash(passwordEncoder.encode(newPassword));
        userMapper.updateById(u);
        // 重置后强制下线全部 token, 防止旧 session 继续使用
        authService.forceLogoutAll(userId);
    }

    @Transactional
    public void adminSetRoles(String userId, List<String> roles) {
        userRoleMapper.delete(new LambdaQueryWrapper<BizUserRole>().eq(BizUserRole::getUserId, userId));
        for (String r : roles) {
            BizUserRole rec = new BizUserRole();
            rec.setUserId(userId);
            rec.setRoleCode(r);
            userRoleMapper.insert(rec);
        }
        // 角色变更必须使旧 token 中的 roles claim 失效, 强制下次重新登录
        authService.forceLogoutAll(userId);
    }

    private String emptyToNull(String s) { return (s == null || s.isBlank()) ? null : s; }
}
