package com.example.flink;

import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.sink.RichSinkFunction;
import org.apache.hadoop.fs.FSDataOutputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;

import java.net.URI;
import java.nio.charset.StandardCharsets;

public class MinioRawJsonSink extends RichSinkFunction<BehaviorEvent> {

    private final String basePath;
    private transient FileSystem fileSystem;
    private transient Path directory;
    private transient BehaviorEventParser parser;

    public MinioRawJsonSink(String basePath) {
        this.basePath = basePath;
    }

    @Override
    public void open(Configuration parameters) throws Exception {
        parser = new BehaviorEventParser();
        fileSystem = FileSystem.get(URI.create(basePath), new org.apache.hadoop.conf.Configuration());
        directory = new Path(basePath);
        if (!fileSystem.exists(directory)) {
            fileSystem.mkdirs(directory);
        }
    }

    @Override
    public void invoke(BehaviorEvent event, Context context) throws Exception {
        Path file = new Path(directory, "event-" + event.eventId() + ".jsonl");
        try (FSDataOutputStream outputStream = fileSystem.create(file, true)) {
            outputStream.write((parser.toJson(event) + "\n").getBytes(StandardCharsets.UTF_8));
        }
    }

    @Override
    public void close() throws Exception {
        if (fileSystem != null) {
            fileSystem.close();
        }
    }
}
