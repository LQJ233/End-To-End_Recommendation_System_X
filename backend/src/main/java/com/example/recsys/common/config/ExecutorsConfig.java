package com.example.recsys.common.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.ThreadPoolExecutor;

/**
 * 线程池隔离 (Bulkhead).
 *
 * 拆成 3 个独立池, 避免任何一种慢请求把 Tomcat 主线程或别的池打满:
 *  - inferenceExecutor : 给推理 RPC 调用使用 (I/O 阻塞);
 *  - snapshotExecutor  : 给推荐快照、Redis 异步写使用 (短任务);
 *  - kafkaFlushExecutor: 给行为日志批量 flush 使用 (顺序写 MySQL).
 *
 * 所有池都配 CallerRunsPolicy, 满载时把任务退回主线程, 避免丢任务.
 * 实际拒绝场景应该极少, 因为 Resilience4j Bulkhead 已经限流过.
 */
@Configuration
@EnableAsync
public class ExecutorsConfig {

    private static final Logger log = LoggerFactory.getLogger(ExecutorsConfig.class);

    @Bean(name = "inferenceExecutor", destroyMethod = "shutdown")
    public ThreadPoolTaskExecutor inferenceExecutor(
            @Value("${app.executor.inference.core:32}") int core,
            @Value("${app.executor.inference.max:64}") int max,
            @Value("${app.executor.inference.queue:200}") int queue,
            @Value("${app.executor.inference.keepAliveSec:60}") int keepAlive) {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(core);
        ex.setMaxPoolSize(max);
        ex.setQueueCapacity(queue);
        ex.setKeepAliveSeconds(keepAlive);
        ex.setThreadNamePrefix("inf-");
        ex.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        ex.setWaitForTasksToCompleteOnShutdown(true);
        ex.setAwaitTerminationSeconds(10);
        ex.initialize();
        log.info("inferenceExecutor: core={} max={} queue={}", core, max, queue);
        return ex;
    }

    @Bean(name = "snapshotExecutor", destroyMethod = "shutdown")
    public ThreadPoolTaskExecutor snapshotExecutor(
            @Value("${app.executor.snapshot.core:4}") int core,
            @Value("${app.executor.snapshot.max:8}") int max,
            @Value("${app.executor.snapshot.queue:1000}") int queue) {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(core);
        ex.setMaxPoolSize(max);
        ex.setQueueCapacity(queue);
        ex.setThreadNamePrefix("snap-");
        ex.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        ex.setWaitForTasksToCompleteOnShutdown(true);
        ex.setAwaitTerminationSeconds(15);
        ex.initialize();
        log.info("snapshotExecutor: core={} max={} queue={}", core, max, queue);
        return ex;
    }

    @Bean(name = "kafkaFlushExecutor", destroyMethod = "shutdown")
    public ThreadPoolTaskExecutor kafkaFlushExecutor(
            @Value("${app.executor.kafkaFlush.core:2}") int core,
            @Value("${app.executor.kafkaFlush.max:4}") int max,
            @Value("${app.executor.kafkaFlush.queue:50}") int queue) {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(core);
        ex.setMaxPoolSize(max);
        ex.setQueueCapacity(queue);
        ex.setThreadNamePrefix("kfl-");
        ex.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        ex.initialize();
        return ex;
    }
}
