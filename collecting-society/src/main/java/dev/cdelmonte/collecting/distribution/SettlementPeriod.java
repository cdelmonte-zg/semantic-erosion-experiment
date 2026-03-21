package dev.cdelmonte.collecting.distribution;

import java.time.LocalDate;

/**
 * Contractual accounting interval (Abrechnungszeitraum) within which usage reports
 * are processed and royalties are distributed to rights holders.
 *
 * Encapsulates the start and end dates of a settlement period and provides
 * the containment check used to qualify usage reports for a distribution run.
 */
public final class SettlementPeriod {

    private final LocalDate start;
    private final LocalDate end;

    public SettlementPeriod(LocalDate start, LocalDate end) {
        if (start == null || end == null) {
            throw new IllegalArgumentException("SettlementPeriod start and end must not be null");
        }
        if (start.isAfter(end)) {
            throw new IllegalArgumentException(
                    "SettlementPeriod start must not be after end: " + start + " > " + end);
        }
        this.start = start;
        this.end = end;
    }

    public LocalDate getStart() { return start; }
    public LocalDate getEnd() { return end; }

    /**
     * Returns true if the given period is fully contained within this period.
     */
    public boolean contains(SettlementPeriod other) {
        return !other.start.isBefore(start) && !other.end.isAfter(end);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof SettlementPeriod)) return false;
        SettlementPeriod that = (SettlementPeriod) o;
        return start.equals(that.start) && end.equals(that.end);
    }

    @Override
    public int hashCode() {
        return 31 * start.hashCode() + end.hashCode();
    }

    @Override
    public String toString() {
        return "SettlementPeriod[" + start + " to " + end + "]";
    }
}
