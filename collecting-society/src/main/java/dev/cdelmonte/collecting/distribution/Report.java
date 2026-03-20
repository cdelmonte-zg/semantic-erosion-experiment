package dev.cdelmonte.collecting.distribution;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * S10: Speculative Generality — abstract base class that only has one subclass.
 * This exists "just in case" other report types are needed in the future,
 * but currently only {@link RoyaltyStatement} extends it.
 */
public abstract class Report {

    private final UUID id;
    private final LocalDateTime generatedAt;

    protected Report(UUID id) {
        this.id = id;
        this.generatedAt = LocalDateTime.now();
    }

    public UUID getId() { return id; }
    public LocalDateTime getGeneratedAt() { return generatedAt; }

    /**
     * Format the report for output. Subclasses must implement.
     */
    public abstract String formatReport();
}
