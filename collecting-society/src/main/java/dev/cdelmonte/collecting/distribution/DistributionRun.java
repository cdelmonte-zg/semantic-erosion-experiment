package dev.cdelmonte.collecting.distribution;

import java.math.BigDecimal;
import java.util.Objects;
import java.util.UUID;

/**
 * Periodic royalty calculation execution for a settlement period.
 * A distribution run processes all usage reports within its settlement period
 * and produces royalty statements for eligible rights holders.
 */
public class DistributionRun {

    private final UUID id;
    private final SettlementPeriod settlementPeriod;
    private DistributionStatus status;
    private BigDecimal totalDistributed;

    public DistributionRun(UUID id, SettlementPeriod settlementPeriod) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.settlementPeriod = Objects.requireNonNull(settlementPeriod, "settlementPeriod must not be null");
        this.status = DistributionStatus.PENDING;
        this.totalDistributed = BigDecimal.ZERO;
    }

    public UUID getId() { return id; }
    public SettlementPeriod getSettlementPeriod() { return settlementPeriod; }
    public DistributionStatus getStatus() { return status; }
    public BigDecimal getTotalDistributed() { return totalDistributed; }

    public void setStatus(DistributionStatus status) {
        this.status = Objects.requireNonNull(status, "status must not be null");
    }

    public void setTotalDistributed(BigDecimal totalDistributed) {
        this.totalDistributed = Objects.requireNonNull(totalDistributed, "totalDistributed must not be null");
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof DistributionRun other)) return false;
        return Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
