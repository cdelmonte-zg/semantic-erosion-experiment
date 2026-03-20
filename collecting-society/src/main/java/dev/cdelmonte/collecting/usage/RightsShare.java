package dev.cdelmonte.collecting.usage;

import java.math.BigDecimal;
import java.util.Objects;

/**
 * A rights holder's fractional share in a musical work, including
 * percentage, role, and territorial scope.
 * Groups the three share-related fields that always vary together.
 */
public final class RightsShare {

    private final BigDecimal percentage;    // 0.0 to 1.0
    private final String holderRole;        // e.g., COMPOSER, PUBLISHER, ARRANGER
    private final String territory;         // e.g., "DE", "WORLDWIDE"

    public RightsShare(BigDecimal percentage, String holderRole, String territory) {
        this.percentage = Objects.requireNonNull(percentage, "percentage must not be null");
        this.holderRole = holderRole;
        this.territory = territory;
    }

    public BigDecimal getPercentage() { return percentage; }
    public String getHolderRole() { return holderRole; }
    public String getTerritory() { return territory; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof RightsShare other)) return false;
        return Objects.equals(percentage, other.percentage)
                && Objects.equals(holderRole, other.holderRole)
                && Objects.equals(territory, other.territory);
    }

    @Override
    public int hashCode() {
        return Objects.hash(percentage, holderRole, territory);
    }

    @Override
    public String toString() {
        return "RightsShare[" + percentage + ", " + holderRole + ", " + territory + "]";
    }
}
