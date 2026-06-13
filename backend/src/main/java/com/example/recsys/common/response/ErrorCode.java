package com.example.recsys.common.response;

public final class ErrorCode {
    private ErrorCode() {}
    public static final int SUCCESS = 0;
    public static final int INVALID_PARAMETER = 400001;
    public static final int UNAUTHORIZED = 401001;
    public static final int FORBIDDEN = 403001;
    public static final int ITEM_NOT_FOUND = 404001;
    public static final int USERNAME_EXISTS = 409001;
    public static final int PHONE_EXISTS = 409002;
    public static final int USER_DISABLED = 423001;
    public static final int TOO_MANY_REQUESTS = 429001;
    public static final int INTERNAL_ERROR = 500001;
    public static final int REDIS_ERROR = 500101;
    public static final int MYSQL_ERROR = 500102;
    public static final int INFERENCE_ERROR = 500201;
    public static final int MILVUS_ERROR = 500202;
    public static final int KAFKA_ERROR = 500301;
}
