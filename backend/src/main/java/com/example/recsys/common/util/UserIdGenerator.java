package com.example.recsys.common.util;

import java.util.concurrent.atomic.AtomicLong;

public final class UserIdGenerator {
    private UserIdGenerator() {}
    private static final AtomicLong SEQ = new AtomicLong(System.currentTimeMillis() % 1_000_000L);
    public static String next() {
        return "u_" + SEQ.incrementAndGet();
    }
}
