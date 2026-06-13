package com.example.recsys.application;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.recsys.application.dto.LoginRequest;
import com.example.recsys.application.dto.LoginResponse;
import com.example.recsys.application.dto.RegisterRequest;
import com.example.recsys.common.config.AppProperties;
import com.example.recsys.common.exception.BusinessException;
import com.example.recsys.common.response.ErrorCode;
import com.example.recsys.common.util.UserIdGenerator;
import com.example.recsys.domain.entity.BizUser;
import com.example.recsys.domain.entity.BizUserLoginLog;
import com.example.recsys.domain.entity.BizUserRole;
import com.example.recsys.infrastructure.mysql.BizUserLoginLogMapper;
import com.example.recsys.infrastructure.mysql.BizUserMapper;
import com.example.recsys.infrastructure.mysql.BizUserRoleMapper;
import com.example.recsys.infrastructure.redis.AuthRedisRepository;
import com.example.recsys.infrastructure.redis.RefreshTokenRepository;
import com.example.recsys.security.AuthUserPrincipal;
import com.example.recsys.security.JwtTokenProvider;
import com.example.recsys.security.SecurityUtils;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class AuthService {

    private final BizUserMapper userMapper;
    private final BizUserRoleMapper userRoleMapper;
    private final BizUserLoginLogMapper loginLogMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider tokenProvider;
    private final AuthRedisRepository authRedis;
    private final RefreshTokenRepository refreshTokenRepo;
    private final LoginAttemptService attemptService;
    private final AppProperties props;

    public AuthService(BizUserMapper userMapper, BizUserRoleMapper userRoleMapper,
                       BizUserLoginLogMapper loginLogMapper, PasswordEncoder passwordEncoder,
                       JwtTokenProvider tokenProvider, AuthRedisRepository authRedis,
                       RefreshTokenRepository refreshTokenRepo,
                       LoginAttemptService attemptService, AppProperties props) {
        this.userMapper = userMapper;
        this.userRoleMapper = userRoleMapper;
        this.loginLogMapper = loginLogMapper;
        this.passwordEncoder = passwordEncoder;
        this.tokenProvider = tokenProvider;
        this.authRedis = authRedis;
        this.refreshTokenRepo = refreshTokenRepo;
        this.attemptService = attemptService;
        this.props = props;
    }

    /**
     * 注册.
     *
     * <p>不再依赖 "select-then-insert" 防重: 并发时两个请求都能通过 select 检查,
     * 第二个会在 INSERT 时被 MySQL 的 UNIQUE 约束拒绝. 这里直接 INSERT, 由
     * {@link com.example.recsys.common.exception.GlobalExceptionHandler#onDuplicateKey}
     * 把 DuplicateKeyException 翻译成 409001 / 409002, 返回准确错误.</p>
     */
    @Transactional
    public BizUser register(RegisterRequest req) {
        BizUser u = new BizUser();
        u.setUserId(UserIdGenerator.next());
        u.setUsername(req.getUsername());
        u.setPasswordHash(passwordEncoder.encode(req.getPassword()));
        u.setNickname(req.getNickname() == null ? req.getUsername() : req.getNickname());
        u.setPhone(emptyToNull(req.getPhone()));
        u.setEmail(emptyToNull(req.getEmail()));
        u.setGender(0);
        u.setUserType(1);
        u.setStatus(1);
        userMapper.insert(u);

        BizUserRole role = new BizUserRole();
        role.setUserId(u.getUserId());
        role.setRoleCode(props.getAuth().getDefaultRole());
        userRoleMapper.insert(role);
        return u;
    }

    public LoginResponse login(LoginRequest req, HttpServletRequest http) {
        String ip = http == null ? null : http.getRemoteAddr();
        String username = req.getUsername();

        // 限流检查: IP 短时间内失败过多 -> 直接 429
        if (attemptService.isIpBlocked(ip)) {
            throw new BusinessException(ErrorCode.TOO_MANY_REQUESTS, "too_many_login_attempts");
        }
        // 账号锁定: 该用户连续失败次数过多 -> 锁定窗口期内一律拒绝
        if (attemptService.isUserLocked(username)) {
            throw new BusinessException(ErrorCode.USER_DISABLED, "account_locked");
        }

        BizUser u = userMapper.selectOne(new LambdaQueryWrapper<BizUser>().eq(BizUser::getUsername, username));
        BizUserLoginLog log = newLoginLog(username, http);
        if (u == null) {
            log.setSuccess(0); log.setFailReason("user_not_found");
            loginLogMapper.insert(log);
            attemptService.recordFailure(ip, username);
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "invalid_credentials");
        }
        log.setUserId(u.getUserId());
        if (u.getStatus() == null || u.getStatus() != 1) {
            log.setSuccess(0); log.setFailReason("user_disabled");
            loginLogMapper.insert(log);
            throw new BusinessException(ErrorCode.USER_DISABLED, "user_disabled");
        }
        if (!passwordEncoder.matches(req.getPassword(), u.getPasswordHash())) {
            log.setSuccess(0); log.setFailReason("bad_password");
            loginLogMapper.insert(log);
            attemptService.recordFailure(ip, username);
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "invalid_credentials");
        }
        List<String> roles = loadRoleCodes(u.getUserId());
        String token = tokenProvider.issue(u.getUserId(), u.getUsername(), roles);
        // 把 tokenId 写入 auth:user:tokens:{userId}, 便于禁用 / 改密时强制下线
        try {
            Claims claims = tokenProvider.parse(token);
            authRedis.trackUserToken(u.getUserId(), claims.getId(), tokenProvider.expiresInSeconds());
        } catch (Exception ignored) {
        }
        u.setLastLoginAt(LocalDateTime.now());
        userMapper.updateById(u);
        log.setSuccess(1);
        loginLogMapper.insert(log);
        attemptService.recordSuccess(username);

        String refreshToken = refreshTokenRepo.issue(u.getUserId());

        LoginResponse resp = new LoginResponse();
        resp.setAccessToken(token);
        resp.setRefreshToken(refreshToken);
        resp.setExpiresIn(tokenProvider.expiresInSeconds());
        resp.setRefreshExpiresIn(props.getAuth().getRefreshTokenExpireDays() * 86400L);
        resp.setUser(new LoginResponse.UserDto(u.getUserId(), u.getUsername(), u.getNickname(), roles));
        return resp;
    }

    /**
     * /auth/refresh: 用 refresh token 换新 access token + 新 refresh token (轮转).
     *
     * - refresh token 一次性, 用完即销毁;
     * - 用户被禁用 / 已删除 -> 拒绝;
     * - 返回新的 access token & refresh token, 前端必须替换本地 token.
     */
    public LoginResponse refresh(String refreshToken) {
        String userId = refreshTokenRepo.consume(refreshToken)
                .orElseThrow(() -> new BusinessException(ErrorCode.UNAUTHORIZED, "invalid_refresh_token"));

        BizUser u = userMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<BizUser>()
                        .eq(BizUser::getUserId, userId));
        if (u == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "user_not_found");
        }
        if (u.getStatus() == null || u.getStatus() != 1) {
            throw new BusinessException(ErrorCode.USER_DISABLED, "user_disabled");
        }

        List<String> roles = loadRoleCodes(u.getUserId());
        String newAccess = tokenProvider.issue(u.getUserId(), u.getUsername(), roles);
        try {
            Claims claims = tokenProvider.parse(newAccess);
            authRedis.trackUserToken(u.getUserId(), claims.getId(), tokenProvider.expiresInSeconds());
        } catch (Exception ignored) {
        }
        String newRefresh = refreshTokenRepo.issue(u.getUserId());

        LoginResponse resp = new LoginResponse();
        resp.setAccessToken(newAccess);
        resp.setRefreshToken(newRefresh);
        resp.setExpiresIn(tokenProvider.expiresInSeconds());
        resp.setRefreshExpiresIn(props.getAuth().getRefreshTokenExpireDays() * 86400L);
        resp.setUser(new LoginResponse.UserDto(u.getUserId(), u.getUsername(), u.getNickname(), roles));
        return resp;
    }

    public void logout(String token) {
        if (token == null) return;
        try {
            Claims claims = tokenProvider.parse(token);
            long remaining = (claims.getExpiration().getTime() - System.currentTimeMillis()) / 1000L;
            if (remaining > 0) authRedis.blacklist(claims.getId(), remaining);
        } catch (Exception ignored) {
        }
    }

    public void invalidateToken(String tokenId) {
        if (tokenId == null) return;
        // 改密码 / 管理员强制下线时调用, 给 token 留 access-token 过期时间的 TTL.
        authRedis.blacklist(tokenId, tokenProvider.expiresInSeconds());
    }

    /** 批量强制下线: access token 全黑名单 + refresh token 全删除. */
    public int forceLogoutAll(String userId) {
        int n = authRedis.invalidateAllForUser(userId, tokenProvider.expiresInSeconds());
        refreshTokenRepo.revokeAllForUser(userId);
        return n;
    }

    public List<String> loadRoleCodes(String userId) {
        return userRoleMapper.selectList(new LambdaQueryWrapper<BizUserRole>().eq(BizUserRole::getUserId, userId))
                .stream().map(BizUserRole::getRoleCode).toList();
    }

    public AuthUserPrincipal requirePrincipal() {
        return SecurityUtils.currentPrincipal()
                .orElseThrow(() -> new BusinessException(ErrorCode.UNAUTHORIZED, "unauthorized"));
    }

    private BizUserLoginLog newLoginLog(String username, HttpServletRequest http) {
        BizUserLoginLog log = new BizUserLoginLog();
        log.setUsername(username);
        log.setLoginType("password");
        if (http != null) {
            log.setClientIp(http.getRemoteAddr());
            String ua = http.getHeader("User-Agent");
            if (ua != null && ua.length() > 500) ua = ua.substring(0, 500);
            log.setUserAgent(ua);
        }
        return log;
    }

    private String emptyToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
