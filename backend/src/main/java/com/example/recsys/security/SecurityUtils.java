package com.example.recsys.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;

public final class SecurityUtils {
    private SecurityUtils() {}
    public static Optional<AuthUserPrincipal> currentPrincipal() {
        Authentication a = SecurityContextHolder.getContext().getAuthentication();
        if (a == null || !a.isAuthenticated()) return Optional.empty();
        Object p = a.getPrincipal();
        return p instanceof AuthUserPrincipal ? Optional.of((AuthUserPrincipal) p) : Optional.empty();
    }
    public static Optional<String> currentUserId() {
        return currentPrincipal().map(AuthUserPrincipal::getUserId);
    }
}
