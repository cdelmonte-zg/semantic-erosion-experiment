package dev.cdelmonte.collecting.distribution;

/**
 * Lifecycle states of a {@link DistributionRun}.
 */
public enum DistributionStatus {
    PENDING,
    RUNNING,
    COMPLETED,
    FAILED
}
