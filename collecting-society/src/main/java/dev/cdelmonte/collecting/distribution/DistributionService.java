package dev.cdelmonte.collecting.distribution;

import dev.cdelmonte.collecting.musicalwork.ExploitationType;
import dev.cdelmonte.collecting.musicalwork.MusicalWork;
import dev.cdelmonte.collecting.musicalwork.MusicalWorkRepository;
import dev.cdelmonte.collecting.rightsholder.RightsHolder;
import dev.cdelmonte.collecting.rightsholder.RightsHolderRepository;
import dev.cdelmonte.collecting.usage.UsageReport;
import dev.cdelmonte.collecting.usage.UsageReportRepository;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Domain service that orchestrates a royalty distribution run.
 *
 * The service delegates eligibility filtering to {@link DistributionKey},
 * tariff rate lookup to {@link TariffClass}, and rights share calculation
 * to {@link RightsShare}. Each logical step of the pipeline is handled
 * by a dedicated private method.
 */
public class DistributionService {

    private final DistributionRunRepository distributionRunRepository;
    private final UsageReportRepository usageReportRepository;
    private final MusicalWorkRepository musicalWorkRepository;
    private final RightsHolderRepository rightsHolderRepository;

    public DistributionService(DistributionRunRepository distributionRunRepository,
                               UsageReportRepository usageReportRepository,
                               MusicalWorkRepository musicalWorkRepository,
                               RightsHolderRepository rightsHolderRepository) {
        this.distributionRunRepository = distributionRunRepository;
        this.usageReportRepository = usageReportRepository;
        this.musicalWorkRepository = musicalWorkRepository;
        this.rightsHolderRepository = rightsHolderRepository;
    }

    /**
     * Executes a distribution run and returns one royalty statement per rights holder.
     *
     * @param distributionRunId the run to execute
     * @param distributionKey   eligibility criteria (period, type filter, revenue threshold)
     * @param currencyCode      currency for the royalty statements
     * @return list of generated royalty statements
     */
    public List<RoyaltyStatement> calculateRoyalties(UUID distributionRunId,
                                                     DistributionKey distributionKey,
                                                     String currencyCode) {
        DistributionRun run = loadAndStartRun(distributionRunId, distributionKey);

        List<UsageReport> eligibleReports = filterEligibleReports(distributionKey);

        Map<UUID, RoyaltyStatement> statementsByHolder =
                computeStatements(eligibleReports, distributionRunId, currencyCode);

        finalizeRun(run, statementsByHolder);

        return new ArrayList<>(statementsByHolder.values());
    }

    /**
     * Convenience method that executes a distribution run for the given period
     * with default parameters: all exploitation types, no minimum revenue, EUR currency.
     */
    public List<RoyaltyStatement> executeDistribution(UUID distributionRunId,
                                                      SettlementPeriod settlementPeriod) {
        DistributionKey defaultKey = new DistributionKey(null, 0.0, settlementPeriod);
        return calculateRoyalties(distributionRunId, defaultKey, "EUR");
    }

    // ── Pipeline steps ────────────────────────────────────────────────────────

    private DistributionRun loadAndStartRun(UUID distributionRunId,
                                            DistributionKey distributionKey) {
        DistributionRun run = distributionRunRepository.findById(distributionRunId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "DistributionRun not found: " + distributionRunId));

        if (run.getStatus() != DistributionStatus.PENDING) {
            throw new IllegalStateException(
                    "DistributionRun must be PENDING, was: " + run.getStatus());
        }

        run.setStatus(DistributionStatus.RUNNING);
        run.setSettlementPeriod(distributionKey.getSettlementPeriod());
        distributionRunRepository.save(run);
        return run;
    }

    private List<UsageReport> filterEligibleReports(DistributionKey distributionKey) {
        List<UsageReport> allReports = usageReportRepository.findBySettlementPeriod(
                distributionKey.getSettlementPeriod());

        List<UsageReport> eligible = new ArrayList<>();
        for (UsageReport report : allReports) {
            if (distributionKey.matches(report)) {
                eligible.add(report);
            }
        }
        return eligible;
    }

    private Map<UUID, RoyaltyStatement> computeStatements(List<UsageReport> reports,
                                                          UUID distributionRunId,
                                                          String currencyCode) {
        Map<UUID, RoyaltyStatement> statementsByHolder = new HashMap<>();

        for (UsageReport report : reports) {
            TariffClass tariff = TariffClass.forExploitationType(report.getExploitationType());
            double grossRoyalty = report.getRevenue() * tariff.rate();

            RightsShare share = report.getRightsShare();
            double holderRoyalty = share.applyTo(grossRoyalty);
            UUID holderId = share.getHolderId();

            RoyaltyStatement statement = statementsByHolder.computeIfAbsent(holderId,
                    id -> createStatement(id, distributionRunId, currencyCode));

            statement.addAmount(holderRoyalty);
        }

        return statementsByHolder;
    }

    private RoyaltyStatement createStatement(UUID holderId, UUID distributionRunId,
                                             String currencyCode) {
        String holderName = rightsHolderRepository.findById(holderId)
                .map(RightsHolder::getName)
                .orElse("Unknown");
        return new RoyaltyStatement(UUID.randomUUID(), distributionRunId,
                holderId, holderName, currencyCode);
    }

    private void finalizeRun(DistributionRun run,
                             Map<UUID, RoyaltyStatement> statementsByHolder) {
        double totalDistributed = statementsByHolder.values().stream()
                .mapToDouble(RoyaltyStatement::getTotalAmount)
                .sum();
        run.setTotalDistributed(totalDistributed);
        run.setStatus(DistributionStatus.COMPLETED);
        distributionRunRepository.save(run);
    }

    // ── Rights share validation (callable independently) ─────────────────────

    /**
     * Validates that the rights share percentage on a usage report matches
     * the share registered against the musical work, and returns the net
     * royalty amount for the rights holder.
     *
     * @throws IllegalArgumentException if the musical work is not found
     * @throws IllegalStateException    if the share percentages do not match
     */
    public double resolveRightsShares(UUID musicalWorkId, RightsShare reportedShare,
                                      double grossAmount) {
        MusicalWork work = musicalWorkRepository.findById(musicalWorkId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "MusicalWork not found: " + musicalWorkId));

        double registeredPercentage = work.getRightsShare().getPercentage();
        if (Math.abs(registeredPercentage - reportedShare.getPercentage()) > 0.001) {
            throw new IllegalStateException(
                    "Rights share mismatch for work " + musicalWorkId
                    + ": registered " + registeredPercentage
                    + " but reported " + reportedShare.getPercentage());
        }

        return reportedShare.applyTo(grossAmount);
    }
}
