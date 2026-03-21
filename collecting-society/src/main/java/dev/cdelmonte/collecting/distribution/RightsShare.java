package dev.cdelmonte.collecting.distribution;

import java.util.UUID;

/**
 * A rights holder's fractional share in a musical work, including their
 * percentage entitlement, role, and territorial scope.
 *
 * Replaces the scattered set of loose fields (rightsHolderId, rightsSharePercentage,
 * rightsHolderRole, shareTerritory) that were duplicated across UsageReport,
 * MusicalWork, and DistributionService method parameters.
 */
public final class RightsShare {

    private final UUID holderId;
    private final double percentage;    // 0.0 to 1.0
    private final String role;          // e.g. COMPOSER, PUBLISHER, ARRANGER
    private final String territory;     // e.g. "DE", "WORLDWIDE"

    public RightsShare(UUID holderId, double percentage, String role, String territory) {
        if (holderId == null) {
            throw new IllegalArgumentException("RightsShare holderId must not be null");
        }
        if (percentage < 0.0 || percentage > 1.0) {
            throw new IllegalArgumentException(
                    "RightsShare percentage must be between 0.0 and 1.0, was: " + percentage);
        }
        this.holderId = holderId;
        this.percentage = percentage;
        this.role = role;
        this.territory = territory;
    }

    public UUID getHolderId() { return holderId; }
    public double getPercentage() { return percentage; }
    public String getRole() { return role; }
    public String getTerritory() { return territory; }

    /**
     * Applies this share's percentage to a gross royalty amount and returns the net amount.
     */
    public double applyTo(double grossAmount) {
        return grossAmount * percentage;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof RightsShare)) return false;
        RightsShare that = (RightsShare) o;
        return Double.compare(that.percentage, percentage) == 0
                && holderId.equals(that.holderId)
                && java.util.Objects.equals(role, that.role)
                && java.util.Objects.equals(territory, that.territory);
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(holderId, percentage, role, territory);
    }

    @Override
    public String toString() {
        return "RightsShare[holder=" + holderId + ", " + (percentage * 100) + "%, role="
                + role + ", territory=" + territory + "]";
    }
}
