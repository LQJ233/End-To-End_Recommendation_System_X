package com.example.flink;

import org.apache.flink.api.common.functions.RuntimeContext;
import org.apache.flink.configuration.Configuration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class MinioRawJsonSinkTest {

    @TempDir
    Path tempDir;

    @Test
    void writesOneJsonLinePerEvent() throws Exception {
        String basePath = tempDir.resolve("behavior_events").toUri().toString();
        MinioRawJsonSink sink = new MinioRawJsonSink(basePath);
        RuntimeContext runtimeContext = mock(RuntimeContext.class);
        when(runtimeContext.getIndexOfThisSubtask()).thenReturn(0);
        sink.setRuntimeContext(runtimeContext);

        sink.open(new Configuration());
        sink.invoke(new BehaviorEvent(
                "evt-1", "user-1", "session-1", 1001L, "click",
                "home", 1, "home_card", "req-1", "rec-1", 1L
        ), null);
        sink.close();

        String content = Files.readString(tempDir.resolve("behavior_events/event-evt-1.jsonl"));
        assertThat(content).contains("\"event_id\":\"evt-1\"");
        assertThat(content).contains("\"item_id\":1001");
    }
}
