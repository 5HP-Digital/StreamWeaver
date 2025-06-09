namespace IPTV.JobWorker.Data;

public class PlaylistSource : ITimestampable
{
    public long Id { get; set; }
    public string Name { get; set; }
    public string Url { get; set; }
    public bool IsEnabled { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public virtual ICollection<PlaylistSourceChannel> Channels { get; init; } = [];
    public virtual ICollection<Job> Jobs { get; init; } = [];
}
