package com.example.backend.common;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

class TraceIdFilterTest {

    private final TraceIdFilter filter = new TraceIdFilter();

    @Test
    void keepsIncomingTraceIdAndClearsMdc() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Trace-Id", "trace-from-client");
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicReference<String> observed = new AtomicReference<>();
        FilterChain chain = (req, res) -> observed.set(MDC.get("traceId"));

        filter.doFilter(request, response, chain);

        assertThat(observed.get()).isEqualTo("trace-from-client");
        assertThat(response.getHeader("X-Trace-Id")).isEqualTo("trace-from-client");
        assertThat(MDC.get("traceId")).isNull();
    }

    @Test
    void generatesTraceIdWhenHeaderIsMissing() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();
        AtomicReference<String> observed = new AtomicReference<>();
        FilterChain chain = (req, res) -> observed.set(MDC.get("traceId"));

        filter.doFilter(request, response, chain);

        assertThat(observed.get()).isNotBlank().hasSize(32);
        assertThat(response.getHeader("X-Trace-Id")).isEqualTo(observed.get());
    }
}
