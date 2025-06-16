namespace IPTV.JobWorker.Data;

public class Provider : ITimestampable
{
    public long Id { get; set; }
    public required string Name { get; set; }
    public required string Url { get; set; }
    public bool IsEnabled { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public virtual ICollection<ProviderStream> Streams { get; init; } = [];
    public virtual ICollection<ProviderSyncJob> Jobs { get; init; } = [];
}
