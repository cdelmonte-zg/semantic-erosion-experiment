package dev.cdelmonte.collecting.distribution;

import dev.cdelmonte.collecting.musicalwork.ExploitationType;
import dev.cdelmonte.collecting.musicalwork.MusicalWork;
import dev.cdelmonte.collecting.musicalwork.MusicalWorkRepository;
import dev.cdelmonte.collecting.rightsholder.RightsHolder;
import dev.cdelmonte.collecting.rightsholder.RightsHolderRepository;
import dev.cdelmonte.collecting.usage.UsageReport;
import dev.cdelmonte.collecting.usage.UsageReportRepository;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * S1: God Class — this service handles royalty calculation, tariff application,
 * claim resolution, distribution key filtering, and statement generation.
 * All logic that should be in separate domain services is concentrated here.
 *
 * Deliberate code smells embedded in this class:
 *   S1  God Class (this entire class)
 *   S2  Long Method (calculateRoyalties)
 *   S3  Long Parameter List (calculateRoyalties signature)
 *   S4  Feature Envy (accessing UsageReport/MusicalWork internals)
 *   S5  Primitive Obsession / Latent SettlementPeriod (raw LocalDate pairs)
 *   S6  Data Clumps / Latent RightsShare (holderId + percentage repeated)
 *   S7  Switch on Type / Latent TariffClass (switch on ExploitationType)
 *   S8  Comments as deodorant (comments papering over complexity)
 *   S9  Latent DistributionKey (inline filtering logic)
 *   S10 Speculative Generality (Report base class used by RoyaltyStatement)
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
     * S2: Long Method — this method does too many things: validates the run,
     * filters usage reports, applies tariffs, resolves claims, and generates statements.
     *
     * S3: Long Parameter List — settlement period dates passed as raw parameters
     * instead of a SettlementPeriod value object.
     *
     * @param distributionRunId  the run to execute
     * @param periodStart        start of the settlement period
     * @param periodEnd          end of the settlement period
     * @param includeOnlyTypes   filter for specific exploitation types (or null for all)
     * @param minimumRevenue     minimum revenue threshold to include a usage report
     * @param currencyCode       currency for the royalty statements
     * @return list of generated royalty statements
     */
    public List<RoyaltyStatement> calculateRoyalties(
            UUID distributionRunId,
            LocalDate periodStart,          // S5: raw date instead of SettlementPeriod
            LocalDate periodEnd,            // S5: raw date instead of SettlementPeriod
            List<ExploitationType> includeOnlyTypes,
            double minimumRevenue,
            String currencyCode) {

        // --- Step 1: Load and validate distribution run ---
        DistributionRun run = distributionRunRepository.findById(distributionRunId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "DistributionRun not found: " + distributionRunId));

        if (!"PENDING".equals(run.getStatus())) {
            throw new IllegalStateException(
                    "DistributionRun must be PENDING, was: " + run.getStatus());
        }

        run.setStatus("RUNNING");
        run.setPeriodStart(periodStart);
        run.setPeriodEnd(periodEnd);
        distributionRunRepository.save(run);

        // --- Step 2: Load usage reports for the settlement period ---
        // S8: Comment papering over the fact that this filtering logic
        //     should be encapsulated in a DistributionKey domain object
        List<UsageReport> allReports =
                usageReportRepository.findByReportingPeriod(periodStart, periodEnd);

        // S9: Latent DistributionKey — inline filtering logic that determines
        //     which usage reports qualify for this distribution run
        List<UsageReport> filteredReports = new ArrayList<>();
        for (UsageReport report : allReports) {
            // S4: Feature Envy — reaching deep into UsageReport internals
            boolean matchesType = (includeOnlyTypes == null)
                    || includeOnlyTypes.contains(report.getExploitationType());
            boolean meetsThreshold = report.getRevenue() >= minimumRevenue;

            // S8: This comment explains what a DistributionKey.matches() would do
            // Check that the report falls within the settlement period boundaries
            boolean withinPeriod =
                    !report.getReportingPeriodStart().isBefore(periodStart)
                    && !report.getReportingPeriodEnd().isAfter(periodEnd);

            if (matchesType && meetsThreshold && withinPeriod) {
                filteredReports.add(report);
            }
        }

        // --- Step 3: Calculate royalties per rights holder ---
        // S8: Comment hiding the fact that this should be a separate method or class
        Map<UUID, RoyaltyStatement> statementsByHolder = new HashMap<>();
        // S6: Parallel maps — additional data clump fields for RightsShare
        Map<UUID, String> workToRole = new HashMap<>();
        Map<UUID, String> workToTerritory = new HashMap<>();
        double totalDistributed = 0.0;

        for (UsageReport report : filteredReports) {
            // S7: Switch on Type / Latent TariffClass — tariff rate determined
            //     by switching on ExploitationType instead of using a TariffClass object
            double tariffRate = applyTariff(report.getExploitationType());

            // S4: Feature Envy — pulling data out of UsageReport to compute here
            double grossRoyalty = report.getRevenue() * tariffRate;

            // S6: Data Clump / Latent RightsShare — accessing the loose share fields
            //     that should be a RightsShare value object
            UUID holderId = report.getRightsHolderId();
            double sharePercentage = report.getRightsSharePercentage();
            String holderRole = report.getRightsHolderRole();
            String territory = report.getShareTerritory();

            // S6: populate parallel maps for the data clump
            workToRole.put(report.getMusicalWorkId(), holderRole);
            workToTerritory.put(report.getMusicalWorkId(), territory);

            // S8: resolveRightsShares — apply the rights holder's share percentage
            double holderRoyalty = grossRoyalty * sharePercentage;

            // Build or update the royalty statement for this holder
            RoyaltyStatement statement = statementsByHolder.get(holderId);
            if (statement == null) {
                // S4: Feature Envy — looking up rights holder name from repository
                String holderName = rightsHolderRepository.findById(holderId)
                        .map(RightsHolder::getName)
                        .orElse("Unknown");

                statement = new RoyaltyStatement(
                        UUID.randomUUID(), distributionRunId, holderId, holderName);
                statement.setCurrency(currencyCode);
                statementsByHolder.put(holderId, statement);
            }

            statement.addAmount(holderRoyalty);
            totalDistributed += holderRoyalty;
        }

        // --- Step 4: Finalize the distribution run ---
        run.setTotalDistributed(totalDistributed);
        run.setStatus("COMPLETED");
        distributionRunRepository.save(run);

        return new ArrayList<>(statementsByHolder.values());
    }

    /**
     * S7: Switch on Type — maps ExploitationType to a tariff rate.
     * A dedicated TariffClass type would encapsulate this mapping,
     * but instead it lives as a switch statement in the service.
     */
    public double applyTariff(ExploitationType exploitationType) {
        // S7: Latent TariffClass — this switch should be a TariffClass lookup
        switch (exploitationType) {
            case BROADCAST:
                return 0.09;
            case PUBLIC_PERFORMANCE:
                return 0.12;
            case MECHANICAL_REPRODUCTION:
                return 0.065;
            case DIGITAL_STREAMING:
                return 0.04;
            case SYNCHRONIZATION:
                return 0.05;
            default:
                throw new IllegalArgumentException(
                        "Unknown exploitation type: " + exploitationType);
        }
    }

    /**
     * S6: Data Clump — this method takes the same loose fields (holderId, sharePercentage)
     * that should be a RightsShare value object.
     * S3: Long Parameter List.
     */
    public double resolveRightsShares(UUID musicalWorkId, UUID rightsHolderId,
                                     double rightsSharePercentage, double grossAmount) {
        // S4: Feature Envy — accessing MusicalWork to validate share
        MusicalWork work = musicalWorkRepository.findById(musicalWorkId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "MusicalWork not found: " + musicalWorkId));

        // S8: Verify the share matches what's registered
        // In a real system, RightsShare would validate itself
        if (Math.abs(work.getRightsSharePercentage() - rightsSharePercentage) > 0.001) {
            throw new IllegalStateException(
                    "Rights share mismatch for work " + musicalWorkId
                    + ": expected " + work.getRightsSharePercentage()
                    + " but got " + rightsSharePercentage);
        }

        return grossAmount * rightsSharePercentage;
    }

    /**
     * Convenience method to execute a distribution run for the given period
     * with default parameters: all exploitation types, no minimum, EUR currency.
     */
    public List<RoyaltyStatement> executeDistribution(UUID distributionRunId,
                                                       LocalDate periodStart,
                                                       LocalDate periodEnd) {
        return calculateRoyalties(
                distributionRunId, periodStart, periodEnd, null, 0.0, "EUR");
    }
}
