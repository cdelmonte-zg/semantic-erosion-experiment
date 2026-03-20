package dev.cdelmonte.collecting.distribution;

import java.time.LocalDate;
import java.util.Objects;

/**
 * Contractual accounting interval (Abrechnungszeitraum) with regulatory implications.
 * Defines the date range over which usage reports are collected and processed
 * in a distribution run.
 */
public final class SettlementPeriod {

    private final LocalDate start;
    private final LocalDate end;

    public SettlementPeriod(LocalDate start, LocalDate end) {
        this.start = Objects.requireNonNull(start, "start must not be null");
        this.end = Objects.requireNonNull(end, "end must not be null");
        if (end.isBefore(start)) {
            throw new IllegalArgumentException("end must not be before start");
        }
    }

    public LocalDate getStart() { return start; }
    public LocalDate getEnd() { return end; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof SettlementPeriod other)) return false;
        return Objects.equals(start, other.start) && Objects.equals(end, other.end);
    }

    @Override
    public int hashCode() {
        return Objects.hash(start, end);
    }

    @Override
    public String toString() {
        return "SettlementPeriod[" + start + " to " + end + "]";
    }
}
