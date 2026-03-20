package dev.cdelmonte.collecting.distribution;

import dev.cdelmonte.collecting.rightsholder.RightsHolder;
import dev.cdelmonte.collecting.rightsholder.RightsHolderRepository;
import dev.cdelmonte.collecting.usage.UsageReport;
import dev.cdelmonte.collecting.usage.UsageReportRepository;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Orchestrates royalty calculation for a distribution run.
 * Loads usage reports for a settlement period, applies tariff rates,
 * and produces royalty statements per rights holder.
 */
public class DistributionService {

    private final DistributionRunRepository distributionRunRepository;
    private final UsageReportRepository usageReportRepository;
    private final RightsHolderRepository rightsHolderRepository;

    public DistributionService(DistributionRunRepository distributionRunRepository,
                               UsageReportRepository usageReportRepository,
                               RightsHolderRepository rightsHolderRepository) {
        this.distributionRunRepository = Objects.requireNonNull(distributionRunRepository, "distributionRunRepository must not be null");
        this.usageReportRepository = Objects.requireNonNull(usageReportRepository, "usageReportRepository must not be null");
        this.rightsHolderRepository = Objects.requireNonNull(rightsHolderRepository, "rightsHolderRepository must not be null");
    }

    /**
     * Calculates royalties for all qualifying usage reports within the run's period.
     *
     * @param distributionRunId  the run to execute
     * @param distributionKey    criteria determining which usage reports are eligible
     * @param currencyCode       currency for the royalty statements
     * @return list of generated royalty statements
     */
    public List<RoyaltyStatement> calculateRoyalties(
            UUID distributionRunId,
            DistributionKey distributionKey,
            String currencyCode) {

        Objects.requireNonNull(distributionRunId, "distributionRunId must not be null");
        Objects.requireNonNull(distributionKey, "distributionKey must not be null");
        Objects.requireNonNull(currencyCode, "currencyCode must not be null");

        DistributionRun run = distributionRunRepository.findById(distributionRunId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "DistributionRun not found: " + distributionRunId));

        if (run.getStatus() != DistributionStatus.PENDING) {
            throw new IllegalStateException(
                    "DistributionRun must be PENDING, was: " + run.getStatus());
        }

        run.setStatus(DistributionStatus.RUNNING);
        distributionRunRepository.save(run);

        List<UsageReport> eligibleReports = usageReportRepository
                .findByReportingPeriod(run.getSettlementPeriod())
                .stream()
                .filter(distributionKey::isEligible)
                .toList();

        Map<UUID, String> holderNames = rightsHolderRepository.findAll().stream()
                .collect(Collectors.toMap(RightsHolder::getId, RightsHolder::getName));

        Map<UUID, RoyaltyStatement> statementsByHolder = new HashMap<>();
        BigDecimal totalDistributed = BigDecimal.ZERO;

        for (UsageReport report : eligibleReports) {
            BigDecimal holderRoyalty = report.getRevenue()
                    .multiply(report.getExploitationType().tariffRate())
                    .multiply(report.getRightsShare().getPercentage());

            UUID holderId = report.getRightsHolderId();
            RoyaltyStatement statement = statementsByHolder.computeIfAbsent(holderId, id -> {
                String holderName = holderNames.getOrDefault(id, "Unknown");
                return new RoyaltyStatement(UUID.randomUUID(), distributionRunId, id, holderName, currencyCode);
            });

            statement.addAmount(holderRoyalty);
            totalDistributed = totalDistributed.add(holderRoyalty);
        }

        run.setTotalDistributed(totalDistributed);
        run.setStatus(DistributionStatus.COMPLETED);
        distributionRunRepository.save(run);

        return List.copyOf(statementsByHolder.values());
    }

    /**
     * Executes a distribution run with default parameters:
     * all exploitation types, no minimum revenue threshold, EUR currency.
     */
    public List<RoyaltyStatement> executeDistribution(UUID distributionRunId) {
        return calculateRoyalties(distributionRunId, DistributionKey.unrestricted(), "EUR");
    }
}
