package com.example.recsys.application;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.recsys.application.dto.*;
import com.example.recsys.common.config.AppProperties;
import com.example.recsys.common.util.RequestIdGenerator;
import com.example.recsys.domain.entity.BizItem;
import com.example.recsys.domain.entity.RecItemPopularity;
import com.example.recsys.domain.entity.RecRequestSnapshot;
import com.example.recsys.infrastructure.client.InferenceClient;
import com.example.recsys.infrastructure.mysql.BizItemMapper;
import com.example.recsys.infrastructure.mysql.RecItemPopularityMapper;
import com.example.recsys.infrastructure.redis.RedisCandidateRepository;
import io.micrometer.observation.annotation.Observed;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class RecommendationService {
    private static final Logger log = LoggerFactory.getLogger(RecommendationService.class);

    private final InferenceClient inferenceClient;
    private final RedisCandidateRepository redisRepo;
    private final BizItemMapper itemMapper;
    private final RecItemPopularityMapper popularityMapper;
    private final AsyncSnapshotService asyncSnapshot;
    private final AppProperties props;

    public RecommendationService(InferenceClient inferenceClient, RedisCandidateRepository redisRepo,
                                 BizItemMapper itemMapper, RecItemPopularityMapper popularityMapper,
                                 AsyncSnapshotService asyncSnapshot, AppProperties props) {
        this.inferenceClient = inferenceClient;
        this.redisRepo = redisRepo;
        this.itemMapper = itemMapper;
        this.popularityMapper = popularityMapper;
        this.asyncSnapshot = asyncSnapshot;
        this.props = props;
    }

    @Observed(name = "recommendation.refresh", contextualName = "rec-refresh")
    public RefreshResult refresh(RefreshRequest req) {
        long t0 = System.currentTimeMillis();
        String scene = req.getScene() == null ? props.getRecommendation().getScene() : req.getScene();
        String requestId = RequestIdGenerator.next();
        String trigger = req.getTriggerType() == null ? "manual" : req.getTriggerType();
        List<String> exclude = req.getExcludeItemIds() == null ? List.of() : req.getExcludeItemIds();

        // 必须用 recommendAsync().join() 才能让 Resilience4j AOP 生效;
        // 在 InferenceClient 内部 wrap 一个 sync 方法会触发 self-invocation, 绕过 Spring 代理.
        InferenceClient.Result inf;
        try {
            inf = inferenceClient.recommendAsync(
                    requestId, req.getUserId(), scene, exclude,
                    props.getFallback().getHotItemSize()).join();
        } catch (Exception e) {
            log.warn("inference future join failed requestId={}: {}", requestId, e.getMessage());
            inf = InferenceClient.Result.empty();
        }

        List<String> itemIds;
        String modelVersion;
        String fallbackType = "none";
        if (inf.success() && !inf.itemIds().isEmpty()) {
            itemIds = filterExclude(inf.itemIds(), exclude);
            modelVersion = inf.modelVersion();
        } else {
            fallbackType = "inference_failed";
            itemIds = fallbackCandidates(req.getUserId(), scene, exclude);
            modelVersion = "fallback";
        }

        redisRepo.replaceCandidates(req.getUserId(), scene, itemIds);
        // 异步落库, 不阻塞返回首页
        asyncSnapshot.writeSnapshot(requestId, req.getUserId(), scene, trigger, itemIds, modelVersion);

        int firstPageSize = Math.min(props.getRecommendation().getPageSize(), itemIds.size());
        List<ItemView> firstPage = lookupItems(itemIds.subList(0, firstPageSize));

        long latency = System.currentTimeMillis() - t0;
        log.info("recommendation.refresh requestId={} userId={} scene={} trigger={} candidateSize={} modelVersion={} latencyMs={} fallback={}",
                requestId, req.getUserId(), scene, trigger, itemIds.size(), modelVersion, latency, fallbackType);
        RefreshResponse resp = new RefreshResponse(modelVersion, itemIds.size(), firstPage);
        return new RefreshResult(requestId, resp);
    }

    public HomePageResponse page(String userId, String scene, int cursor, int size) {
        String s = scene == null ? props.getRecommendation().getScene() : scene;
        long total = redisRepo.candidateSize(userId, s);
        if (total == 0) {
            RefreshRequest req = new RefreshRequest();
            req.setUserId(userId); req.setScene(s); req.setTriggerType("cache_miss");
            refresh(req);
            total = redisRepo.candidateSize(userId, s);
        }
        List<String> ids = redisRepo.readPage(userId, s, cursor, size);
        boolean hasMore = (long) (cursor + ids.size()) < total;
        return new HomePageResponse(s, cursor + ids.size(), hasMore, lookupItems(ids));
    }

    public boolean confirmExposure(ExposureRequest req) {
        String scene = props.getRecommendation().getScene();
        redisRepo.markExposed(req.getUserId(), req.getRequestId(), req.getItemIds());
        redisRepo.removeFromCache(req.getUserId(), req.getItemIds());
        long total = redisRepo.candidateSize(req.getUserId(), scene);
        long exposed = redisRepo.exposedSize(req.getUserId(), req.getRequestId());
        return total > 0 && exposed >= total;
    }

    public List<ItemView> lookupItems(List<String> itemIds) {
        if (itemIds == null || itemIds.isEmpty()) return List.of();
        List<BizItem> rows = itemMapper.selectList(
                new LambdaQueryWrapper<BizItem>()
                        .in(BizItem::getItemId, itemIds)
                        .eq(BizItem::getStatus, 1));
        Map<String, ItemView> byId = rows.stream()
                .collect(Collectors.toMap(BizItem::getItemId, ItemView::from, (a, b) -> a));
        List<ItemView> result = new ArrayList<>(itemIds.size());
        for (String id : itemIds) {
            ItemView v = byId.get(id);
            if (v != null) result.add(v);
        }
        return result;
    }

    private List<String> filterExclude(List<String> ids, List<String> exclude) {
        if (exclude == null || exclude.isEmpty()) return ids;
        Set<String> ex = new HashSet<>(exclude);
        List<String> out = new ArrayList<>(ids.size());
        for (String id : ids) if (!ex.contains(id)) out.add(id);
        return out;
    }

    private List<String> fallbackCandidates(String userId, String scene, List<String> exclude) {
        if (props.getFallback().isUseOldRedisCandidate()) {
            List<String> old = redisRepo.readAll(userId, scene);
            if (!old.isEmpty()) return filterExclude(old, exclude);
        }
        if (props.getFallback().isEnableHotItems()) {
            Set<String> hot = redisRepo.hotItems(props.getFallback().getHotItemSize());
            if (!hot.isEmpty()) return filterExclude(new ArrayList<>(hot), exclude);
            List<RecItemPopularity> rows = popularityMapper.selectList(
                    new LambdaQueryWrapper<RecItemPopularity>()
                            .orderByDesc(RecItemPopularity::getScore)
                            .last("LIMIT " + props.getFallback().getHotItemSize()));
            return filterExclude(rows.stream().map(RecItemPopularity::getItemId).toList(), exclude);
        }
        return List.of();
    }

    public record RefreshResult(String requestId, RefreshResponse response) {}
}
