package dev.cdelmonte.collecting.distribution;

import java.util.UUID;

/**
 * Periodic royalty calculation execution for a settlement period.
 * A distribution run processes all usage reports within its settlement period
 * and produces royalty statements for eligible rights holders.
 */
public class DistributionRun {

    private final UUID id;
    private DistributionStatus status;
    private SettlementPeriod settlementPeriod;
    private double totalDistributed;

    public DistributionRun(UUID id, SettlementPeriod settlementPeriod) {
        this.id = id;
        this.settlementPeriod = settlementPeriod;
        this.status = DistributionStatus.PENDING;
        this.totalDistributed = 0.0;
    }

    public UUID getId() { return id; }
    public DistributionStatus getStatus() { return status; }
    public SettlementPeriod getSettlementPeriod() { return settlementPeriod; }
    public double getTotalDistributed() { return totalDistributed; }

    public void setStatus(DistributionStatus status) { this.status = status; }
    public void setSettlementPeriod(SettlementPeriod settlementPeriod) {
        this.settlementPeriod = settlementPeriod;
    }
    public void setTotalDistributed(double totalDistributed) {
        this.totalDistributed = totalDistributed;
    }
}
