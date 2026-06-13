package com.example.recsys;

import com.example.recsys.common.config.LocalConfigInitializer;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@MapperScan("com.example.recsys.infrastructure.mysql")
@EnableScheduling
public class RecsysApplication {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(RecsysApplication.class);
        app.addInitializers(new LocalConfigInitializer());
        app.run(args);
    }
}
