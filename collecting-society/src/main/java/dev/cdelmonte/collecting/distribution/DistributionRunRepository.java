package dev.cdelmonte.collecting.distribution;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for persisting and retrieving {@link DistributionRun} aggregates.
 */
public interface DistributionRunRepository {

    Optional<DistributionRun> findById(UUID id);

    List<DistributionRun> findByStatus(String status);

    void save(DistributionRun distributionRun);
}
