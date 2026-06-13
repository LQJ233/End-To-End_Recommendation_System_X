package com.example.recsys.common.config;

import org.apache.hc.client5.http.config.ConnectionConfig;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.util.TimeValue;
import org.apache.hc.core5.util.Timeout;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import io.micrometer.tracing.Tracer;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.util.List;

/**
 * Apache HttpClient5 池化客户端, 替换默认 SimpleClientHttpRequestFactory.
 * SimpleClientHttpRequestFactory 每次都开新连接, 高并发下会迅速耗尽端口.
 */
@Configuration
public class HttpClientConfig {

    @Bean
    public CloseableHttpClient inferenceHttpClient(
            @Value("${app.inference.timeoutMs:3000}") int timeoutMs,
            @Value("${app.inference.maxTotal:200}") int maxTotal,
            @Value("${app.inference.maxPerRoute:100}") int maxPerRoute) {
        PoolingHttpClientConnectionManager pool = new PoolingHttpClientConnectionManager();
        pool.setMaxTotal(maxTotal);
        pool.setDefaultMaxPerRoute(maxPerRoute);
        pool.setDefaultConnectionConfig(ConnectionConfig.custom()
                .setConnectTimeout(Timeout.ofMilliseconds(timeoutMs))
                .setSocketTimeout(Timeout.ofMilliseconds(timeoutMs))
                .setValidateAfterInactivity(TimeValue.ofSeconds(30))
                .build());

        RequestConfig req = RequestConfig.custom()
                .setConnectionRequestTimeout(Timeout.ofMilliseconds(500))
                .setResponseTimeout(Timeout.ofMilliseconds(timeoutMs))
                .build();

        return HttpClients.custom()
                .setConnectionManager(pool)
                .setDefaultRequestConfig(req)
                .evictExpiredConnections()
                .evictIdleConnections(TimeValue.ofMinutes(1))
                .build();
    }

    @Bean(name = "inferenceRestTemplate")
    public RestTemplate inferenceRestTemplate(CloseableHttpClient inferenceHttpClient,
                                              ObjectProvider<Tracer> tracerProvider) {
        HttpComponentsClientHttpRequestFactory f = new HttpComponentsClientHttpRequestFactory(inferenceHttpClient);
        RestTemplate tpl = new RestTemplate(f);
        Tracer tracer = tracerProvider.getIfAvailable();
        if (tracer != null) {
            tpl.setInterceptors(List.of(new TraceHeaderInterceptor(tracer)));
        }
        return tpl;
    }
}
