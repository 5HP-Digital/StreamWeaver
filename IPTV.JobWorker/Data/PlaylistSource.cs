namespace IPTV.JobWorker.Data;

public class PlaylistSource
{
    public long Id { get; set; }
    public string Name { get; set; }
    public string Url { get; set; }
    public bool IsEnabled { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public ICollection<PlaylistSourceChannel> Channels { get; init; } = [];
}
