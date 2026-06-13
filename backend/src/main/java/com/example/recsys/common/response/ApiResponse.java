package com.example.recsys.common.response;

public class ApiResponse<T> {
    private int code;
    private String message;
    private String requestId;
    private T data;

    public ApiResponse() {}
    public ApiResponse(int code, String message, String requestId, T data) {
        this.code = code; this.message = message; this.requestId = requestId; this.data = data;
    }

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(0, "success", null, data);
    }
    public static <T> ApiResponse<T> ok(T data, String requestId) {
        return new ApiResponse<>(0, "success", requestId, data);
    }
    public static <T> ApiResponse<T> error(int code, String message) {
        return new ApiResponse<>(code, message, null, null);
    }
    public static <T> ApiResponse<T> error(int code, String message, String requestId) {
        return new ApiResponse<>(code, message, requestId, null);
    }

    public int getCode() { return code; } public void setCode(int v) { code = v; }
    public String getMessage() { return message; } public void setMessage(String v) { message = v; }
    public String getRequestId() { return requestId; } public void setRequestId(String v) { requestId = v; }
    public T getData() { return data; } public void setData(T v) { data = v; }
}
