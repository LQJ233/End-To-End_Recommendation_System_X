package com.example.recsys.common.config;

import io.micrometer.tracing.Tracer;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;

import java.io.IOException;
import java.util.Locale;

/**
 * 把当前 trace 上下文以 W3C traceparent 写到下游 HTTP 请求,
 * 这样 Python 推理服务的 OTEL 中间件能把它当作 parent span 继续上报.
 */
public class TraceHeaderInterceptor implements ClientHttpRequestInterceptor {

    private final Tracer tracer;

    public TraceHeaderInterceptor(Tracer tracer) {
        this.tracer = tracer;
    }

    @Override
    public ClientHttpResponse intercept(HttpRequest request, byte[] body,
                                        ClientHttpRequestExecution execution) throws IOException {
        var span = tracer.currentSpan();
        if (span != null) {
            var ctx = span.context();
            String traceparent = String.format(Locale.ROOT,
                    "00-%s-%s-01", ctx.traceId(), ctx.spanId());
            request.getHeaders().add("traceparent", traceparent);
        }
        return execution.execute(request, body);
    }
}
