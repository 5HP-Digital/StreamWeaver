namespace IPTV.JobWorker.Data;

public abstract class Job : ITimestampable
{
    public long Id { get; set; }

    public JobType Type { get; set; }

    public Guid JobId { get; set; }

    public JobState State { get; set; } = JobState.Queued;
    
    public string? StatusDescription { get; set; }

    public DateTime? LastAttemptStartedAt { get; set; }
    
    public int AttemptCount { get; set; }
    
    public int? MaxAttempts { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}