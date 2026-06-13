package com.example.recsys.common.util;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicInteger;

public final class RequestIdGenerator {
    private RequestIdGenerator() {}
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");
    private static final AtomicInteger SEQ = new AtomicInteger(0);

    public static String next() {
        int seq = SEQ.incrementAndGet() & 0xfff;
        return "rec_" + LocalDateTime.now().format(FMT) + String.format("%03d", seq);
    }
}
