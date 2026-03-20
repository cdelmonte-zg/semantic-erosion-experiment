package dev.cdelmonte.collecting.musicalwork;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for persisting and retrieving {@link MusicalWork} aggregates.
 */
public interface MusicalWorkRepository {

    Optional<MusicalWork> findById(UUID id);

    Optional<MusicalWork> findByIswcCode(String iswcCode);

    List<MusicalWork> findByRightsHolderId(UUID rightsHolderId);

    List<MusicalWork> findAll();

    void save(MusicalWork musicalWork);
}
