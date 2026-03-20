package dev.cdelmonte.collecting.usage;

import dev.cdelmonte.collecting.distribution.SettlementPeriod;
import dev.cdelmonte.collecting.musicalwork.ExploitationType;

import java.math.BigDecimal;
import java.util.Objects;
import java.util.UUID;

/**
 * Documented exploitation of a musical work by a licensee.
 * Each usage report records when and how a work was exploited,
 * along with the revenue generated from that exploitation.
 */
public class UsageReport {

    private final UUID id;
    private final UUID musicalWorkId;
    private final ExploitationType exploitationType;
    private final int playCount;
    private final BigDecimal revenue;

    private final SettlementPeriod reportingPeriod;

    private final UUID rightsHolderId;
    private final RightsShare rightsShare;

    private final String licensee;

    public UsageReport(UUID id, UUID musicalWorkId, ExploitationType exploitationType,
                       int playCount, BigDecimal revenue,
                       SettlementPeriod reportingPeriod,
                       UUID rightsHolderId, RightsShare rightsShare,
                       String licensee) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.musicalWorkId = Objects.requireNonNull(musicalWorkId, "musicalWorkId must not be null");
        this.exploitationType = Objects.requireNonNull(exploitationType, "exploitationType must not be null");
        this.playCount = playCount;
        this.revenue = Objects.requireNonNull(revenue, "revenue must not be null");
        this.reportingPeriod = Objects.requireNonNull(reportingPeriod, "reportingPeriod must not be null");
        this.rightsHolderId = Objects.requireNonNull(rightsHolderId, "rightsHolderId must not be null");
        this.rightsShare = Objects.requireNonNull(rightsShare, "rightsShare must not be null");
        this.licensee = licensee;
    }

    public UUID getId() { return id; }
    public UUID getMusicalWorkId() { return musicalWorkId; }
    public ExploitationType getExploitationType() { return exploitationType; }
    public int getPlayCount() { return playCount; }
    public BigDecimal getRevenue() { return revenue; }
    public SettlementPeriod getReportingPeriod() { return reportingPeriod; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public RightsShare getRightsShare() { return rightsShare; }
    public String getLicensee() { return licensee; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UsageReport other)) return false;
        return Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
