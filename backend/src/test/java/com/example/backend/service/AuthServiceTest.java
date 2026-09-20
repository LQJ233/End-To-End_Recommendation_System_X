package com.example.backend.service;

import com.example.backend.common.BusinessException;
import com.example.backend.common.ErrorCode;
import com.example.backend.dto.AuthResponse;
import com.example.backend.dto.LoginRequest;
import com.example.backend.dto.RegisterRequest;
import com.example.backend.entity.User;
import com.example.backend.mapper.UserMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserMapper userMapper;

    private PasswordEncoder passwordEncoder;
    private AuthService authService;

    @BeforeEach
    void setUp() {
        passwordEncoder = new BCryptPasswordEncoder();
        authService = new AuthService(
                userMapper,
                passwordEncoder,
                "test-secret-key-for-unit-tests-1234567890",
                60_000L
        );
    }

    @Test
    void registerCreatesUserAndReturnsToken() {
        RegisterRequest request = new RegisterRequest("new_user", "password123");
        when(userMapper.selectCount(any())).thenReturn(0L);
        doAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(42L);
            return 1;
        }).when(userMapper).insert(any(User.class));

        AuthResponse response = authService.register(request);

        assertThat(response.userId()).isEqualTo(42L);
        assertThat(response.username()).isEqualTo("new_user");
        assertThat(response.token()).isNotBlank();
        verify(userMapper).insert(any(User.class));
    }

    @Test
    void registerRejectsDuplicateUsername() {
        when(userMapper.selectCount(any())).thenReturn(1L);

        assertThatThrownBy(() -> authService.register(new RegisterRequest("taken", "password123")))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.USERNAME_EXISTS);
    }

    @Test
    void loginReturnsTokenForValidCredentials() {
        User user = new User();
        user.setId(7L);
        user.setUsername("alice");
        user.setPasswordHash(passwordEncoder.encode("secret123"));
        when(userMapper.selectOne(any())).thenReturn(user);

        AuthResponse response = authService.login(new LoginRequest("alice", "secret123"));

        assertThat(response.userId()).isEqualTo(7L);
        assertThat(response.username()).isEqualTo("alice");
        assertThat(response.token()).isNotBlank();
    }

    @Test
    void loginRejectsUnknownUser() {
        when(userMapper.selectOne(any())).thenReturn(null);

        assertThatThrownBy(() -> authService.login(new LoginRequest("missing", "secret123")))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.USER_NOT_FOUND);
    }

    @Test
    void loginRejectsWrongPassword() {
        User user = new User();
        user.setId(7L);
        user.setUsername("alice");
        user.setPasswordHash(passwordEncoder.encode("correct-password"));
        when(userMapper.selectOne(any())).thenReturn(user);

        assertThatThrownBy(() -> authService.login(new LoginRequest("alice", "wrong-password")))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.PASSWORD_ERROR);
    }
}
