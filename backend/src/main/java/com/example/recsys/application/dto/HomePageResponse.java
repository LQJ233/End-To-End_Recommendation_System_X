package com.example.recsys.application.dto;

import java.util.List;

public class HomePageResponse {
    private String scene;
    private int cursor;
    private boolean hasMore;
    private List<ItemView> items;
    public HomePageResponse(String scene, int cursor, boolean hasMore, List<ItemView> items) {
        this.scene = scene; this.cursor = cursor; this.hasMore = hasMore; this.items = items;
    }
    public String getScene() { return scene; }
    public int getCursor() { return cursor; }
    public boolean isHasMore() { return hasMore; }
    public List<ItemView> getItems() { return items; }
}
