package com.example.recsys.common.config;

import org.springframework.context.ApplicationContextInitializer;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.env.MapPropertySource;
import org.yaml.snakeyaml.Yaml;

import java.io.File;
import java.io.FileInputStream;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Load conf/application-local.yml and inject every leaf under "app." prefix so the rest of the
 * app can use ${app.mysql.host} style placeholders. Source of truth for connections / paths.
 */
public class LocalConfigInitializer implements ApplicationContextInitializer<ConfigurableApplicationContext> {

    @Override
    public void initialize(ConfigurableApplicationContext ctx) {
        String configPath = System.getProperty("app.configPath",
                ctx.getEnvironment().getProperty("app.configPath", "E:/End-To-End_Recommendation_System_X/conf/application-local.yml"));
        File file = new File(configPath);
        if (!file.exists()) {
            return;
        }
        try (FileInputStream in = new FileInputStream(file)) {
            Object loaded = new Yaml().load(in);
            if (!(loaded instanceof Map<?, ?> root)) {
                return;
            }
            Map<String, Object> flat = new HashMap<>();
            flatten("app", root, flat);
            ctx.getEnvironment().getPropertySources()
                    .addFirst(new MapPropertySource("ecommerceRecsysLocalConf", flat));
        } catch (Exception e) {
            System.err.println("[LocalConfigInitializer] failed: " + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private static void flatten(String prefix, Object node, Map<String, Object> out) {
        if (node instanceof Map<?, ?> map) {
            for (Map.Entry<?, ?> e : map.entrySet()) {
                flatten(prefix + "." + e.getKey(), e.getValue(), out);
            }
        } else if (node instanceof java.util.List<?> list) {
            out.put(prefix, list);
            int i = 0;
            for (Object item : list) {
                flatten(prefix + "[" + i + "]", item, out);
                i++;
            }
        } else {
            out.put(prefix, node);
        }
    }
}
