package dev.cdelmonte.collecting.distribution;

import java.util.UUID;

/**
 * Per-holder financial result produced by a distribution run.
 * Each royalty statement captures the computed royalty amount
 * for a specific rights holder within a distribution run.
 *
 * S10: Extends {@link Report} — speculative generality base class.
 */
public class RoyaltyStatement extends Report {

    private final UUID distributionRunId;
    private final UUID rightsHolderId;
    private final String rightsHolderName;
    private double totalAmount;
    private String currency;

    public RoyaltyStatement(UUID id, UUID distributionRunId,
                            UUID rightsHolderId, String rightsHolderName) {
        super(id);
        this.distributionRunId = distributionRunId;
        this.rightsHolderId = rightsHolderId;
        this.rightsHolderName = rightsHolderName;
        this.totalAmount = 0.0;
        this.currency = "EUR";
    }

    public UUID getDistributionRunId() { return distributionRunId; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public String getRightsHolderName() { return rightsHolderName; }
    public double getTotalAmount() { return totalAmount; }
    public String getCurrency() { return currency; }

    public void addAmount(double amount) { this.totalAmount += amount; }
    public void setCurrency(String currency) { this.currency = currency; }

    @Override
    public String formatReport() {
        return String.format("RoyaltyStatement[holder=%s, amount=%.2f %s, run=%s]",
                rightsHolderName, totalAmount, currency, distributionRunId);
    }
}
