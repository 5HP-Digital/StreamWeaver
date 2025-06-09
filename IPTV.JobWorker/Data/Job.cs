namespace IPTV.JobWorker.Data;

public class Job : ITimestampable
{
    public long Id { get; set; }

    public required Guid JobId { get; set; }

    public required JobState State { get; set; }

    public int AttemptCount { get; set; }
    
    public string? Error { get; set; }

    public required string Context { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }
}