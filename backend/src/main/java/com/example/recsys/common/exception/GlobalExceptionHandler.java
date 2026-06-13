package com.example.recsys.common.exception;

import com.example.recsys.common.response.ApiResponse;
import com.example.recsys.common.response.ErrorCode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 把业务异常映射到 HTTP 状态码 + 统一 body, 前端可以同时根据 HTTP status (axios)
 * 和 body.code (具体业务码) 做处理.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<?>> onBusiness(BusinessException e) {
        log.warn("business exception: code={} msg={}", e.getCode(), e.getMessage());
        int http = mapHttpStatus(e.getCode());
        return ResponseEntity.status(http).body(ApiResponse.error(e.getCode(), e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<?>> onValidate(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getAllErrors().isEmpty()
                ? "invalid_parameter"
                : e.getBindingResult().getAllErrors().get(0).getDefaultMessage();
        return ResponseEntity.badRequest().body(ApiResponse.error(ErrorCode.INVALID_PARAMETER, msg));
    }

    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ApiResponse<?>> onAuth(AuthenticationException e) {
        return ResponseEntity.status(401).body(ApiResponse.error(ErrorCode.UNAUTHORIZED, "unauthorized"));
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiResponse<?>> onForbidden(AccessDeniedException e) {
        return ResponseEntity.status(403).body(ApiResponse.error(ErrorCode.FORBIDDEN, "forbidden"));
    }

    /**
     * 并发注册时, 唯一约束触发 DuplicateKeyException; 必须比 onAny 优先处理,
     * 才能返回正确的 409 而非 500.
     */
    @ExceptionHandler(DuplicateKeyException.class)
    public ResponseEntity<ApiResponse<?>> onDuplicateKey(DuplicateKeyException e) {
        String msg = e.getMostSpecificCause().getMessage();
        if (msg == null) msg = "";
        int code = ErrorCode.INTERNAL_ERROR;
        String label = "duplicate_key";
        if (msg.contains("uk_biz_user_username")) {
            code = ErrorCode.USERNAME_EXISTS; label = "username_exists";
        } else if (msg.contains("uk_biz_user_phone")) {
            code = ErrorCode.PHONE_EXISTS; label = "phone_exists";
        } else if (msg.contains("uk_biz_user_email")) {
            code = ErrorCode.PHONE_EXISTS; label = "email_exists";
        }
        log.warn("duplicate key: code={} cause={}", code, msg);
        return ResponseEntity.status(409).body(ApiResponse.error(code, label));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<?>> onAny(Exception e) {
        log.error("unhandled exception", e);
        return ResponseEntity.status(500).body(ApiResponse.error(ErrorCode.INTERNAL_ERROR, "internal_error"));
    }

    private int mapHttpStatus(int code) {
        if (code == ErrorCode.UNAUTHORIZED) return 401;
        if (code == ErrorCode.FORBIDDEN) return 403;
        if (code == ErrorCode.ITEM_NOT_FOUND) return 404;
        if (code == ErrorCode.USERNAME_EXISTS || code == ErrorCode.PHONE_EXISTS) return 409;
        if (code == ErrorCode.USER_DISABLED) return 423;
        if (code == ErrorCode.TOO_MANY_REQUESTS) return 429;
        if (code >= 500000) return 500;
        if (code >= 400000) return 400;
        return 200;
    }
}
