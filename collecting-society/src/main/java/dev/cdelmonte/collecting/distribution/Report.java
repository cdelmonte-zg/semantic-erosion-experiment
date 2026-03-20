package dev.cdelmonte.collecting.distribution;

import java.time.LocalDateTime;
import java.util.Objects;
import java.util.UUID;

/**
 * Base class for generated reports, capturing the report id and generation timestamp.
 */
public abstract class Report {

    private final UUID id;
    private final LocalDateTime generatedAt;

    protected Report(UUID id) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.generatedAt = LocalDateTime.now();
    }

    public UUID getId() { return id; }
    public LocalDateTime getGeneratedAt() { return generatedAt; }

    /**
     * Format the report for output. Subclasses must implement.
     */
    public abstract String formatReport();

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Report other)) return false;
        return Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
