package dev.cdelmonte.collecting.musicalwork;

import dev.cdelmonte.collecting.distribution.RightsShare;

import java.util.UUID;

/**
 * Registered copyrighted composition managed by the society.
 * Each musical work has an ISWC code and is associated with a rights share
 * that records the rights holder's entitlement, role, and territory.
 */
public class MusicalWork {

    private final UUID id;
    private String title;
    private String iswcCode;        // International Standard Musical Work Code
    private RightsShare rightsShare;

    public MusicalWork(UUID id, String title, String iswcCode, RightsShare rightsShare) {
        this.id = id;
        this.title = title;
        this.iswcCode = iswcCode;
        this.rightsShare = rightsShare;
    }

    public UUID getId() { return id; }
    public String getTitle() { return title; }
    public String getIswcCode() { return iswcCode; }
    public RightsShare getRightsShare() { return rightsShare; }

    public void setTitle(String title) { this.title = title; }
    public void setIswcCode(String iswcCode) { this.iswcCode = iswcCode; }
    public void setRightsShare(RightsShare rightsShare) { this.rightsShare = rightsShare; }
}
