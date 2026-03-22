package dev.cdelmonte.collecting.distribution;

import java.time.LocalDate;
import java.util.UUID;

/**
 * Periodic royalty calculation execution for a settlement period.
 * A distribution run processes all usage reports within its settlement period
 * and produces royalty statements for eligible rights holders.
 */
public class DistributionRun {

    private final UUID id;
    private String status;          // PENDING, RUNNING, COMPLETED, FAILED

    // S5: Latent SettlementPeriod — represented as raw LocalDate pair
    //     instead of a dedicated SettlementPeriod value object
    private LocalDate periodStart;
    private LocalDate periodEnd;

    private double totalDistributed;

    public DistributionRun(UUID id, LocalDate periodStart, LocalDate periodEnd) {
        this.id = id;
        this.periodStart = periodStart;
        this.periodEnd = periodEnd;
        this.status = "PENDING";
        this.totalDistributed = 0.0;
    }

    public UUID getId() { return id; }
    public String getStatus() { return status; }
    public LocalDate getPeriodStart() { return periodStart; }
    public LocalDate getPeriodEnd() { return periodEnd; }
    public double getTotalDistributed() { return totalDistributed; }

    public void setStatus(String status) { this.status = status; }
    public void setPeriodStart(LocalDate periodStart) { this.periodStart = periodStart; }
    public void setPeriodEnd(LocalDate periodEnd) { this.periodEnd = periodEnd; }
    public void setTotalDistributed(double totalDistributed) {
        this.totalDistributed = totalDistributed;
    }
}
