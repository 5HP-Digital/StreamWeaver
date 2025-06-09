namespace IPTV.JobWorker.Data;

public class PlaylistSyncJob : ITimestampable
{
    public long Id { get; set; }

    public Guid JobId { get; set; }

    public JobState State { get; set; }
    
    public string? StatusDescription { get; set; }

    public DateTime? LastAttemptStartedAt { get; set; }
    
    public int AttemptCount { get; set; }
    
    public int? MaxAttempts { get; set; }

    public bool AllowChannelAutoDeletion { get; set; } = true;

    public required string Context { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }

    public virtual required PlaylistSource Source { get; set; }
}