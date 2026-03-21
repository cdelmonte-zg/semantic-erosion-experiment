package dev.cdelmonte.collecting.usage;

import dev.cdelmonte.collecting.distribution.RightsShare;
import dev.cdelmonte.collecting.distribution.SettlementPeriod;
import dev.cdelmonte.collecting.musicalwork.ExploitationType;

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
    private final double revenue;
    private final SettlementPeriod reportingPeriod;
    private final RightsShare rightsShare;
    private final String licensee;

    public UsageReport(UUID id, UUID musicalWorkId, ExploitationType exploitationType,
                       int playCount, double revenue,
                       SettlementPeriod reportingPeriod,
                       RightsShare rightsShare,
                       String licensee) {
        this.id = id;
        this.musicalWorkId = musicalWorkId;
        this.exploitationType = exploitationType;
        this.playCount = playCount;
        this.revenue = revenue;
        this.reportingPeriod = reportingPeriod;
        this.rightsShare = rightsShare;
        this.licensee = licensee;
    }

    public UUID getId() { return id; }
    public UUID getMusicalWorkId() { return musicalWorkId; }
    public ExploitationType getExploitationType() { return exploitationType; }
    public int getPlayCount() { return playCount; }
    public double getRevenue() { return revenue; }
    public SettlementPeriod getReportingPeriod() { return reportingPeriod; }
    public RightsShare getRightsShare() { return rightsShare; }
    public String getLicensee() { return licensee; }
}
