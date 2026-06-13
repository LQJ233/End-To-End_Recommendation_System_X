package com.example.recsys.common.util;

import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class UserIdGeneratorTest {

    @Test
    void hasPrefix() {
        assertTrue(UserIdGenerator.next().startsWith("u_"));
    }

    @Test
    void monotonicAndUnique() {
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < 5_000; i++) {
            assertTrue(seen.add(UserIdGenerator.next()));
        }
    }
}
