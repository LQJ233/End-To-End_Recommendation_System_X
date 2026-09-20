package com.example.backend.controller;

import com.example.backend.dto.EventReportRequest;
import com.example.backend.service.EventService;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class EventControllerTest extends ControllerTestSupport {

    @Test
    void reportDelegatesToService() throws Exception {
        EventService eventService = mock(EventService.class);
        MockMvc mvc = mockMvc(new EventController(eventService));

        mvc.perform(post("/api/v1/events")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "eventId":"evt-1",
                                  "userId":"u1",
                                  "sessionId":"s1",
                                  "itemId":1001,
                                  "eventType":"expose",
                                  "page":"home",
                                  "position":1,
                                  "source":"card_exposure",
                                  "eventTime":1700000000000
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));

        verify(eventService).report(any(EventReportRequest.class));
    }
}
