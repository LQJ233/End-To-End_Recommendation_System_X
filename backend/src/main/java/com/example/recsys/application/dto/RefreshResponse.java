package com.example.recsys.application.dto;

import java.util.List;

public class RefreshResponse {
    private String modelVersion;
    private int candidateSize;
    private List<ItemView> items;
    public RefreshResponse(String modelVersion, int candidateSize, List<ItemView> items) {
        this.modelVersion = modelVersion; this.candidateSize = candidateSize; this.items = items;
    }
    public String getModelVersion() { return modelVersion; }
    public int getCandidateSize() { return candidateSize; }
    public List<ItemView> getItems() { return items; }
}
