package com.example.backend.controller;

import com.example.backend.dto.HomeResponse;
import com.example.backend.service.HomeService;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class HomeControllerTest extends ControllerTestSupport {

    @Test
    void homeUsesAnonymousUserByDefault() throws Exception {
        HomeService homeService = mock(HomeService.class);
        when(homeService.getHome(anyString()))
                .thenReturn(new HomeResponse("req-1", "rec-1", "anonymous", List.of()));
        MockMvc mvc = mockMvc(new HomeController(homeService));

        mvc.perform(get("/api/v1/home"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.userId").value("anonymous"));

        ArgumentCaptor<String> userIdCaptor = ArgumentCaptor.forClass(String.class);
        verify(homeService).getHome(userIdCaptor.capture());
        assertThat(userIdCaptor.getValue()).isEqualTo("anonymous");
    }

    @Test
    void homeUsesHeaderUserWhenPresent() throws Exception {
        HomeService homeService = mock(HomeService.class);
        when(homeService.getHome("user-9"))
                .thenReturn(new HomeResponse("req-9", "rec-9", "user-9", List.of()));
        MockMvc mvc = mockMvc(new HomeController(homeService));

        mvc.perform(get("/api/v1/home").header("X-User-Id", "user-9"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.userId").value("user-9"));
    }
}
