package dev.cdelmonte.collecting.distribution;

import dev.cdelmonte.collecting.musicalwork.ExploitationType;
import dev.cdelmonte.collecting.usage.UsageReport;

import java.util.List;

/**
 * Algorithm determining which usage reports are eligible for inclusion in a
 * distribution run (GEMA: Verteilungsschluessel).
 *
 * A DistributionKey encapsulates the three eligibility conditions that were
 * previously scattered as anonymous boolean checks inside calculateRoyalties():
 * exploitation type filter, minimum revenue threshold, and settlement period containment.
 */
public final class DistributionKey {

    private final List<ExploitationType> allowedTypes;  // null means all types are allowed
    private final double minimumRevenue;
    private final SettlementPeriod settlementPeriod;

    public DistributionKey(List<ExploitationType> allowedTypes,
                           double minimumRevenue,
                           SettlementPeriod settlementPeriod) {
        if (settlementPeriod == null) {
            throw new IllegalArgumentException("DistributionKey requires a SettlementPeriod");
        }
        this.allowedTypes = allowedTypes;
        this.minimumRevenue = minimumRevenue;
        this.settlementPeriod = settlementPeriod;
    }

    /**
     * Returns true if the usage report qualifies for inclusion in the distribution run
     * governed by this key.
     */
    public boolean matches(UsageReport report) {
        boolean matchesType = (allowedTypes == null)
                || allowedTypes.contains(report.getExploitationType());

        boolean meetsThreshold = report.getRevenue() >= minimumRevenue;

        boolean withinPeriod = settlementPeriod.contains(report.getReportingPeriod());

        return matchesType && meetsThreshold && withinPeriod;
    }

    public SettlementPeriod getSettlementPeriod() { return settlementPeriod; }
    public double getMinimumRevenue() { return minimumRevenue; }
    public List<ExploitationType> getAllowedTypes() { return allowedTypes; }

    @Override
    public String toString() {
        return "DistributionKey[period=" + settlementPeriod
                + ", minRevenue=" + minimumRevenue
                + ", types=" + (allowedTypes == null ? "ALL" : allowedTypes) + "]";
    }
}
