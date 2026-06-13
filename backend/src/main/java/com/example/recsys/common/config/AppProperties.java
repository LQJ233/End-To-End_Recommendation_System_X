package com.example.recsys.common.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private Server server = new Server();
    private Inference inference = new Inference();
    private Auth auth = new Auth();
    private Recommendation recommendation = new Recommendation();
    private Fallback fallback = new Fallback();
    private Kafka kafka = new Kafka();

    public static class Server {
        private int backendPort = 8080;
        private int inferencePort = 9000;
        private int trackPort = 8088;
        public int getBackendPort() { return backendPort; } public void setBackendPort(int v) { backendPort = v; }
        public int getInferencePort() { return inferencePort; } public void setInferencePort(int v) { inferencePort = v; }
        public int getTrackPort() { return trackPort; } public void setTrackPort(int v) { trackPort = v; }
    }
    public static class Inference {
        private String baseUrl = "http://localhost:9000/api/v1";
        private int timeoutMs = 3000;
        public String getBaseUrl() { return baseUrl; } public void setBaseUrl(String v) { baseUrl = v; }
        public int getTimeoutMs() { return timeoutMs; } public void setTimeoutMs(int v) { timeoutMs = v; }
    }
    public static class Auth {
        private String jwtSecret = "change_me_to_a_long_random_secret_change_me_to_a_long_random_secret";
        private int accessTokenExpireMinutes = 120;
        private int refreshTokenExpireDays = 30;
        private int bcryptStrength = 10;
        private String defaultRole = "USER";
        private String adminRole = "ADMIN";
        private boolean enableTokenBlacklist = true;
        public String getJwtSecret() { return jwtSecret; } public void setJwtSecret(String v) { jwtSecret = v; }
        public int getAccessTokenExpireMinutes() { return accessTokenExpireMinutes; } public void setAccessTokenExpireMinutes(int v) { accessTokenExpireMinutes = v; }
        public int getRefreshTokenExpireDays() { return refreshTokenExpireDays; } public void setRefreshTokenExpireDays(int v) { refreshTokenExpireDays = v; }
        public int getBcryptStrength() { return bcryptStrength; } public void setBcryptStrength(int v) { bcryptStrength = v; }
        public String getDefaultRole() { return defaultRole; } public void setDefaultRole(String v) { defaultRole = v; }
        public String getAdminRole() { return adminRole; } public void setAdminRole(String v) { adminRole = v; }
        public boolean isEnableTokenBlacklist() { return enableTokenBlacklist; } public void setEnableTokenBlacklist(boolean v) { enableTokenBlacklist = v; }
    }
    public static class Recommendation {
        private String scene = "home";
        private int pageSize = 20;
        private int candidateTtlHours = 24;
        private int cacheRecallMaxSize = 50;
        private int cacheRecallMaxTimes = 10;
        private int cacheRecallTtlDays = 3;
        public String getScene() { return scene; } public void setScene(String v) { scene = v; }
        public int getPageSize() { return pageSize; } public void setPageSize(int v) { pageSize = v; }
        public int getCandidateTtlHours() { return candidateTtlHours; } public void setCandidateTtlHours(int v) { candidateTtlHours = v; }
        public int getCacheRecallMaxSize() { return cacheRecallMaxSize; } public void setCacheRecallMaxSize(int v) { cacheRecallMaxSize = v; }
        public int getCacheRecallMaxTimes() { return cacheRecallMaxTimes; } public void setCacheRecallMaxTimes(int v) { cacheRecallMaxTimes = v; }
        public int getCacheRecallTtlDays() { return cacheRecallTtlDays; } public void setCacheRecallTtlDays(int v) { cacheRecallTtlDays = v; }
    }
    public static class Fallback {
        private boolean enableHotItems = true;
        private int hotItemSize = 500;
        private boolean useOldRedisCandidate = true;
        public boolean isEnableHotItems() { return enableHotItems; } public void setEnableHotItems(boolean v) { enableHotItems = v; }
        public int getHotItemSize() { return hotItemSize; } public void setHotItemSize(int v) { hotItemSize = v; }
        public boolean isUseOldRedisCandidate() { return useOldRedisCandidate; } public void setUseOldRedisCandidate(boolean v) { useOldRedisCandidate = v; }
    }
    public static class Kafka {
        private String bootstrapServers = "localhost:9092";
        private String behaviorTopic = "user_behavior_log";
        private String consumerGroup = "End-To-End_Recommendation_System_X-consumer";
        public String getBootstrapServers() { return bootstrapServers; } public void setBootstrapServers(String v) { bootstrapServers = v; }
        public String getBehaviorTopic() { return behaviorTopic; } public void setBehaviorTopic(String v) { behaviorTopic = v; }
        public String getConsumerGroup() { return consumerGroup; } public void setConsumerGroup(String v) { consumerGroup = v; }
    }

    public static class Cors {
        // 鍏佽鐨?origin 鍒楄〃 (鏀寔 * 閫氶厤绗︽ā寮? 浣嗙敓浜х幆澧冨繀椤荤簿纭啓鍩熷悕)
        private java.util.List<String> allowedOrigins = java.util.List.of("http://localhost:5173");
        public java.util.List<String> getAllowedOrigins() { return allowedOrigins; } public void setAllowedOrigins(java.util.List<String> v) { allowedOrigins = v; }
    }

    private Cors cors = new Cors();
    public Cors getCors() { return cors; } public void setCors(Cors v) { cors = v; }

    public Server getServer() { return server; } public void setServer(Server v) { server = v; }
    public Inference getInference() { return inference; } public void setInference(Inference v) { inference = v; }
    public Auth getAuth() { return auth; } public void setAuth(Auth v) { auth = v; }
    public Recommendation getRecommendation() { return recommendation; } public void setRecommendation(Recommendation v) { recommendation = v; }
    public Fallback getFallback() { return fallback; } public void setFallback(Fallback v) { fallback = v; }
    public Kafka getKafka() { return kafka; } public void setKafka(Kafka v) { kafka = v; }
}
