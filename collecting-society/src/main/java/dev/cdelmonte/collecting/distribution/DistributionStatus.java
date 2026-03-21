package dev.cdelmonte.collecting.distribution;

/**
 * Lifecycle state of a {@link DistributionRun}.
 */
public enum DistributionStatus {
    PENDING,
    RUNNING,
    COMPLETED,
    FAILED
}
