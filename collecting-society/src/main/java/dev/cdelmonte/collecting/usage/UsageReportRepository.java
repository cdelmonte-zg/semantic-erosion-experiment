package dev.cdelmonte.collecting.usage;

import dev.cdelmonte.collecting.distribution.SettlementPeriod;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for persisting and retrieving {@link UsageReport} aggregates.
 */
public interface UsageReportRepository {

    Optional<UsageReport> findById(UUID id);

    List<UsageReport> findByMusicalWorkId(UUID musicalWorkId);

    List<UsageReport> findBySettlementPeriod(SettlementPeriod period);

    List<UsageReport> findAll();

    void save(UsageReport usageReport);
}
