package com.example.flink;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class MySqlCdcJobTest {

    @Test
    void cdcCoversAllBusinessTables() {
        assertThat(MySqlCdcJob.TABLES).containsExactly(
                "ecommerce.behavior_event",
                "ecommerce.item",
                "ecommerce.user",
                "ecommerce.recommendation_log",
                "ecommerce.model_registry",
                "ecommerce.event_outbox",
                "ecommerce.pipeline_watermark"
        );
    }
}
