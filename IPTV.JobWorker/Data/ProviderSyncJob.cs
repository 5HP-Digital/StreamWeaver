namespace IPTV.JobWorker.Data;

public class ProviderSyncJob : ITimestampable
{
    public long Id { get; set; }

    public Guid JobId { get; set; }

    public JobState State { get; set; } = JobState.Queued;
    
    public string? StatusDescription { get; set; }

    public DateTime? LastAttemptStartedAt { get; set; }
    
    public int AttemptCount { get; set; }
    
    public int? MaxAttempts { get; set; }

    public bool AllowStreamAutoDeletion { get; set; } = true;

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }

    public virtual required Provider Provider { get; set; }
}