package dev.cdelmonte.collecting.usage;

import dev.cdelmonte.collecting.musicalwork.ExploitationType;

import java.time.LocalDate;
import java.util.UUID;

/**
 * Documented exploitation of a musical work by a licensee.
 * Each usage report records when and how a work was exploited,
 * along with the revenue generated from that exploitation.
 *
 * S5: Latent SettlementPeriod — period represented as raw LocalDate pair.
 * S6: Latent RightsShare — share fields are data clumps (holderId + percentage).
 */
public class UsageReport {

    private final UUID id;
    private final UUID musicalWorkId;
    private final ExploitationType exploitationType;
    private final int playCount;
    private final double revenue;

    // S5: Latent SettlementPeriod — raw dates instead of value object
    private final LocalDate reportingPeriodStart;
    private final LocalDate reportingPeriodEnd;

    // S6: Data Clump — rights holder info repeated here instead of
    //     referencing a RightsShare or using the MusicalWork's data
    private final UUID rightsHolderId;
    private final double rightsSharePercentage;
    private final String rightsHolderRole;   // e.g., COMPOSER, PUBLISHER, ARRANGER
    private final String shareTerritory;     // e.g., "DE", "WORLDWIDE"

    private final String licensee;

    public UsageReport(UUID id, UUID musicalWorkId, ExploitationType exploitationType,
                       int playCount, double revenue,
                       LocalDate reportingPeriodStart, LocalDate reportingPeriodEnd,
                       UUID rightsHolderId, double rightsSharePercentage,
                       String rightsHolderRole, String shareTerritory,
                       String licensee) {
        this.id = id;
        this.musicalWorkId = musicalWorkId;
        this.exploitationType = exploitationType;
        this.playCount = playCount;
        this.revenue = revenue;
        this.reportingPeriodStart = reportingPeriodStart;
        this.reportingPeriodEnd = reportingPeriodEnd;
        this.rightsHolderId = rightsHolderId;
        this.rightsSharePercentage = rightsSharePercentage;
        this.rightsHolderRole = rightsHolderRole;
        this.shareTerritory = shareTerritory;
        this.licensee = licensee;
    }

    /**
     * Factory method — creates a UsageReport from raw data.
     */
    public static UsageReport of(UUID id, UUID musicalWorkId, ExploitationType exploitationType,
                                  int playCount, double revenue,
                                  LocalDate reportingPeriodStart, LocalDate reportingPeriodEnd,
                                  UUID rightsHolderId, double rightsSharePercentage,
                                  String rightsHolderRole, String shareTerritory,
                                  String licensee) {
        return new UsageReport(id, musicalWorkId, exploitationType,
                playCount, revenue, reportingPeriodStart, reportingPeriodEnd,
                rightsHolderId, rightsSharePercentage, rightsHolderRole, shareTerritory,
                licensee);
    }

    public UUID getId() { return id; }
    public UUID getMusicalWorkId() { return musicalWorkId; }
    public ExploitationType getExploitationType() { return exploitationType; }
    public int getPlayCount() { return playCount; }
    public double getRevenue() { return revenue; }
    public LocalDate getReportingPeriodStart() { return reportingPeriodStart; }
    public LocalDate getReportingPeriodEnd() { return reportingPeriodEnd; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public double getRightsSharePercentage() { return rightsSharePercentage; }
    public String getRightsHolderRole() { return rightsHolderRole; }
    public String getShareTerritory() { return shareTerritory; }
    public String getLicensee() { return licensee; }
}
