package com.example.backend.common;

public enum ErrorCode {
    BAD_REQUEST(30001, "参数错误"),
    UNAUTHORIZED(20001, "未登录"),
    FORBIDDEN(20002, "权限不足"),
    USERNAME_EXISTS(30002, "用户名已存在"),
    USER_NOT_FOUND(30003, "用户不存在"),
    PASSWORD_ERROR(30004, "密码错误"),
    ITEM_NOT_FOUND(40001, "商品不存在"),
    EVENT_ID_EXISTS(30005, "事件已存在"),
    INTERNAL_ERROR(50000, "系统内部错误");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}
