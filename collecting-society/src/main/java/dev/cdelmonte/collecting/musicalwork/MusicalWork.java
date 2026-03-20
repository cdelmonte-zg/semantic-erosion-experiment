package dev.cdelmonte.collecting.musicalwork;

import java.math.BigDecimal;
import java.util.Objects;
import java.util.UUID;

/**
 * Registered copyrighted composition managed by the society.
 * Each musical work has an ISWC code and belongs to one or more rights holders.
 */
public class MusicalWork {

    private final UUID id;
    private String title;
    private String iswcCode;        // International Standard Musical Work Code

    private UUID rightsHolderId;
    private BigDecimal rightsSharePercentage;   // 0.0 to 1.0

    public MusicalWork(UUID id, String title, String iswcCode,
                       UUID rightsHolderId, BigDecimal rightsSharePercentage) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.title = Objects.requireNonNull(title, "title must not be null");
        this.iswcCode = iswcCode;
        this.rightsHolderId = rightsHolderId;
        this.rightsSharePercentage = rightsSharePercentage;
    }

    public UUID getId() { return id; }
    public String getTitle() { return title; }
    public String getIswcCode() { return iswcCode; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public BigDecimal getRightsSharePercentage() { return rightsSharePercentage; }

    public void setTitle(String title) {
        this.title = Objects.requireNonNull(title, "title must not be null");
    }
    public void setIswcCode(String iswcCode) { this.iswcCode = iswcCode; }
    public void setRightsHolderId(UUID rightsHolderId) { this.rightsHolderId = rightsHolderId; }
    public void setRightsSharePercentage(BigDecimal rightsSharePercentage) {
        this.rightsSharePercentage = rightsSharePercentage;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MusicalWork other)) return false;
        return Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
