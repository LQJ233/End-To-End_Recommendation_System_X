package com.example.recsys.application;

import com.example.recsys.domain.entity.RecRequestSnapshot;
import com.example.recsys.infrastructure.mysql.RecRequestSnapshotMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 把 rec_request_snapshot 落库挪到 @Async 线程, 不阻塞推荐主链路.
 *
 * 失败只打日志, 不抛出 — 推荐已经返回给前端, 重试没价值;
 * 监控这里的失败率即可.
 */
@Service
public class AsyncSnapshotService {
    private static final Logger log = LoggerFactory.getLogger(AsyncSnapshotService.class);

    private final RecRequestSnapshotMapper snapshotMapper;
    private final ObjectMapper mapper = new ObjectMapper();

    public AsyncSnapshotService(RecRequestSnapshotMapper snapshotMapper) {
        this.snapshotMapper = snapshotMapper;
    }

    @Async("snapshotExecutor")
    public void writeSnapshot(String requestId, String userId, String scene, String triggerType,
                              List<String> itemIds, String modelVersion) {
        try {
            RecRequestSnapshot s = new RecRequestSnapshot();
            s.setRequestId(requestId);
            s.setUserId(userId);
            s.setScene(scene);
            s.setTriggerType(triggerType);
            s.setItemIdsJson(mapper.writeValueAsString(itemIds));
            s.setModelVersion(modelVersion);
            snapshotMapper.insert(s);
        } catch (Exception e) {
            log.warn("async snapshot write failed requestId={}: {}", requestId, e.getMessage());
        }
    }
}
