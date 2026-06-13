package com.example.recsys.common.util;

import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class RequestIdGeneratorTest {

    @Test
    void hasExpectedPrefixAndLength() {
        String id = RequestIdGenerator.next();
        assertTrue(id.startsWith("rec_"), "must start with rec_");
        assertEquals(21, id.length(), "rec_ + 14 digits + 3 digits");
    }

    @Test
    void isUniqueUnderTightLoop() {
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < 10_000; i++) {
            assertTrue(seen.add(RequestIdGenerator.next()),
                    "duplicate request id detected at i=" + i);
        }
    }
}
