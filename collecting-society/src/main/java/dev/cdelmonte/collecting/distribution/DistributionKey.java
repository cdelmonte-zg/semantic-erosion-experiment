package dev.cdelmonte.collecting.distribution;

import dev.cdelmonte.collecting.musicalwork.ExploitationType;
import dev.cdelmonte.collecting.usage.UsageReport;

import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * Algorithm determining how collected royalties are allocated among eligible rights holders.
 * GEMA: Verteilungsschluessel.
 * Encapsulates the filtering criteria applied to usage reports before royalty calculation.
 */
public final class DistributionKey {

    private final Set<ExploitationType> eligibleTypes;  // empty set means all types are eligible
    private final BigDecimal minimumRevenue;

    public DistributionKey(List<ExploitationType> eligibleTypes, BigDecimal minimumRevenue) {
        this.eligibleTypes = Set.copyOf(Objects.requireNonNull(eligibleTypes, "eligibleTypes must not be null"));
        this.minimumRevenue = Objects.requireNonNull(minimumRevenue, "minimumRevenue must not be null");
    }

    /** A DistributionKey that includes all exploitation types with no minimum revenue threshold. */
    public static DistributionKey unrestricted() {
        return new DistributionKey(List.of(), BigDecimal.ZERO);
    }

    public Set<ExploitationType> getEligibleTypes() { return eligibleTypes; }
    public BigDecimal getMinimumRevenue() { return minimumRevenue; }

    public boolean isEligible(UsageReport report) {
        if (!eligibleTypes.isEmpty() && !eligibleTypes.contains(report.getExploitationType())) {
            return false;
        }
        return report.getRevenue().compareTo(minimumRevenue) >= 0;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof DistributionKey other)) return false;
        return Objects.equals(eligibleTypes, other.eligibleTypes)
                && Objects.equals(minimumRevenue, other.minimumRevenue);
    }

    @Override
    public int hashCode() {
        return Objects.hash(eligibleTypes, minimumRevenue);
    }
}
