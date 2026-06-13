package com.example.recsys.infrastructure.client;

import com.example.recsys.common.config.AppProperties;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * Python 推理服务的 RPC 封装.
 *
 * <p>三层保护栈:</p>
 * <ol>
 *   <li>{@code inferenceExecutor} 有界队列 = 隔板(Bulkhead)</li>
 *   <li>{@link TimeLimiter} 单次 3s 超时</li>
 *   <li>{@link CircuitBreaker} 失败率阈值打开熔断, 进入 fallback</li>
 * </ol>
 *
 * <p><b>重要:</b> 外部调用者必须直接调 {@link #recommendAsync} 才能让 Spring AOP 代理生效;
 * 不要在本类内部再封装 sync wrapper, 否则 self-invocation 会绕过代理, 保护栈全失效.</p>
 */
@Component
public class InferenceClient {
    private static final Logger log = LoggerFactory.getLogger(InferenceClient.class);
    public static final String CB_NAME = "inference";

    private final RestTemplate restTemplate;
    private final ObjectMapper mapper = new ObjectMapper();
    private final AppProperties props;
    private final Executor executor;

    public InferenceClient(@Qualifier("inferenceRestTemplate") RestTemplate restTemplate,
                           AppProperties props,
                           @Qualifier("inferenceExecutor") Executor executor) {
        this.restTemplate = restTemplate;
        this.props = props;
        this.executor = executor;
    }

    /**
     * 异步推理调用. 外部 Bean (如 RecommendationService) 必须直接调本方法,
     * 然后 .join() 或 .get(timeout) 等待结果.
     */
    @CircuitBreaker(name = CB_NAME, fallbackMethod = "fallback")
    @TimeLimiter(name = CB_NAME)
    public CompletableFuture<Result> recommendAsync(String requestId, String userId, String scene,
                                                    List<String> excludeItemIds, int recallSize) {
        return CompletableFuture.supplyAsync(
                () -> doCall(requestId, userId, scene, excludeItemIds, recallSize),
                executor);
    }

    private Result doCall(String requestId, String userId, String scene,
                          List<String> excludeItemIds, int recallSize) {
        String url = props.getInference().getBaseUrl() + "/inference/recommend";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("requestId", requestId);
        body.put("userId", userId);
        body.put("scene", scene);
        body.put("recallSize", recallSize);
        body.put("excludeItemIds", excludeItemIds == null ? List.of() : excludeItemIds);
        body.put("recallOptions", Map.of(
                "enableVectorRecall", true,
                "enableLbsRecall", true,
                "enableTagRecall", true
        ));
        try {
            String resp = restTemplate.postForObject(url, new HttpEntity<>(body, headers), String.class);
            JsonNode root = mapper.readTree(resp);
            if (root.path("code").asInt(-1) != 0) {
                log.warn("inference non-zero code requestId={} body={}", requestId, resp);
                throw new InferenceRpcException("inference_non_zero_code");
            }
            JsonNode data = root.path("data");
            List<String> items = new ArrayList<>();
            for (JsonNode it : data.path("items")) {
                items.add(it.path("itemId").asText());
            }
            return new Result(true, data.path("modelVersion").asText(null), items);
        } catch (InferenceRpcException e) {
            throw e;
        } catch (Exception e) {
            log.warn("inference rpc failed requestId={}: {}", requestId, e.getMessage());
            throw new InferenceRpcException("inference_rpc_failure: " + e.getMessage(), e);
        }
    }

    /** Resilience4j fallback - 与 recommendAsync 签名一致, 末位 Throwable. */
    @SuppressWarnings("unused")
    private CompletableFuture<Result> fallback(String requestId, String userId, String scene,
                                               List<String> excludeItemIds, int recallSize,
                                               Throwable ex) {
        log.warn("inference fallback requestId={} cause={}", requestId, ex.toString());
        return CompletableFuture.completedFuture(Result.empty());
    }

    public record Result(boolean success, String modelVersion, List<String> itemIds) {
        public static Result empty() { return new Result(false, null, List.of()); }
    }

    public static class InferenceRpcException extends RuntimeException {
        public InferenceRpcException(String message) { super(message); }
        public InferenceRpcException(String message, Throwable cause) { super(message, cause); }
    }
}
