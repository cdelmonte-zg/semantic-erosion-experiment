package dev.cdelmonte.collecting.distribution;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Per-holder financial result produced by a distribution run.
 * Each royalty statement captures the computed royalty amount
 * for a specific rights holder within a distribution run.
 * GEMA: Abrechnung.
 */
public class RoyaltyStatement {

    private final UUID id;
    private final LocalDateTime generatedAt;
    private final UUID distributionRunId;
    private final UUID rightsHolderId;
    private final String rightsHolderName;
    private double totalAmount;
    private String currency;

    public RoyaltyStatement(UUID id, UUID distributionRunId,
                            UUID rightsHolderId, String rightsHolderName,
                            String currency) {
        this.id = id;
        this.generatedAt = LocalDateTime.now();
        this.distributionRunId = distributionRunId;
        this.rightsHolderId = rightsHolderId;
        this.rightsHolderName = rightsHolderName;
        this.totalAmount = 0.0;
        this.currency = currency;
    }

    public UUID getId() { return id; }
    public LocalDateTime getGeneratedAt() { return generatedAt; }
    public UUID getDistributionRunId() { return distributionRunId; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public String getRightsHolderName() { return rightsHolderName; }
    public double getTotalAmount() { return totalAmount; }
    public String getCurrency() { return currency; }

    public void addAmount(double amount) { this.totalAmount += amount; }

    public String formatReport() {
        return String.format("RoyaltyStatement[holder=%s, amount=%.2f %s, run=%s]",
                rightsHolderName, totalAmount, currency, distributionRunId);
    }
}
