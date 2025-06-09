namespace IPTV.JobWorker.Data;

public class PlaylistSource : ITimestampable
{
    public long Id { get; set; }
    public required string Name { get; set; }
    public required string Url { get; set; }
    public bool IsEnabled { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public virtual ICollection<PlaylistSourceChannel> Channels { get; init; } = [];
    public virtual ICollection<PlaylistSyncJob> Jobs { get; init; } = [];
}
