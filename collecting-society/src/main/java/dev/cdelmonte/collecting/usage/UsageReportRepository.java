package dev.cdelmonte.collecting.usage;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for persisting and retrieving {@link UsageReport} aggregates.
 */
public interface UsageReportRepository {

    Optional<UsageReport> findById(UUID id);

    List<UsageReport> findByMusicalWorkId(UUID musicalWorkId);

    List<UsageReport> findByReportingPeriod(LocalDate start, LocalDate end);

    List<UsageReport> findAll();

    void save(UsageReport usageReport);
}
