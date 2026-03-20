package dev.cdelmonte.collecting.musicalwork;

import java.util.UUID;

/**
 * Registered copyrighted composition managed by the society.
 * Each musical work has an ISWC code and belongs to one or more rights holders.
 */
public class MusicalWork {

    private final UUID id;
    private String title;
    private String iswcCode;        // International Standard Musical Work Code

    // S6: Data Clump — rights holder share represented as loose fields
    //     instead of a dedicated RightsShare value object
    private UUID rightsHolderId;
    private double rightsSharePercentage;   // 0.0 to 1.0

    public MusicalWork(UUID id, String title, String iswcCode,
                       UUID rightsHolderId, double rightsSharePercentage) {
        this.id = id;
        this.title = title;
        this.iswcCode = iswcCode;
        this.rightsHolderId = rightsHolderId;
        this.rightsSharePercentage = rightsSharePercentage;
    }

    public UUID getId() { return id; }
    public String getTitle() { return title; }
    public String getIswcCode() { return iswcCode; }
    public UUID getRightsHolderId() { return rightsHolderId; }
    public double getRightsSharePercentage() { return rightsSharePercentage; }

    public void setTitle(String title) { this.title = title; }
    public void setIswcCode(String iswcCode) { this.iswcCode = iswcCode; }
    public void setRightsHolderId(UUID rightsHolderId) { this.rightsHolderId = rightsHolderId; }
    public void setRightsSharePercentage(double rightsSharePercentage) {
        this.rightsSharePercentage = rightsSharePercentage;
    }
}
