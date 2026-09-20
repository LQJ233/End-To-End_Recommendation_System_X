package com.example.backend.service;

public class RecServingUnavailableException extends RuntimeException {

    public RecServingUnavailableException(String message) {
        super(message);
    }

    public RecServingUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}
