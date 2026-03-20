package dev.cdelmonte.collecting.distribution;

import java.math.BigDecimal;
import java.util.Objects;
import java.util.UUID;

/**
 * Per-holder financial result produced by a distribution run.
 * Each royalty statement captures the computed royalty amount
 * for a specific rights holder within a distribution run.
 */
public class RoyaltyStatement extends Report {

    private final UUID distributionRunId;
    private final UUID rightsHolderId;
    private final String rightsHolderName;
    private final String currency;
    private BigDecimal totalAmount;

    public RoyaltyStatement(UUID id, UUID distributionRunId,
                            UUID rightsHolderId, String rightsHolderName, String currency) {
        super(id);
        this.distributionRunId = Objects.requireNonNull(distributionRunId, "distributionRunId must not be null");
        this.rightsHolderId = Objects.requireNonNull(rightsHolderId, "rightsHolderId must not be null");
        this.rightsHolderName = Objects.requireNonNull(rightsHolderName, "rightsHolderName must not be null");
        this.currency = Objects.requireNonNull(currency, "currency must not be null");
        this.totalAmount = BigDecimal.ZERO;
    }

    public UUID getDistributionRunId() { return distributionRunId; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public String getRightsHolderName() { return rightsHolderName; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public String getCurrency() { return currency; }

    public void addAmount(BigDecimal amount) { this.totalAmount = this.totalAmount.add(amount); }

    @Override
    public String formatReport() {
        return String.format("RoyaltyStatement[holder=%s, amount=%.2f %s, run=%s]",
                rightsHolderName, totalAmount, currency, distributionRunId);
    }
}
