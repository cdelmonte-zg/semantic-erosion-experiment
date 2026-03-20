package dev.cdelmonte.collecting.rightsholder;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for persisting and retrieving {@link RightsHolder} aggregates.
 */
public interface RightsHolderRepository {

    Optional<RightsHolder> findById(UUID id);

    Optional<RightsHolder> findByIpiNumber(String ipiNumber);

    List<RightsHolder> findAll();

    void save(RightsHolder rightsHolder);
}
