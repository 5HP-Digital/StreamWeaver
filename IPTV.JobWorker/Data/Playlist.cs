namespace IPTV.JobWorker.Data;

public class Playlist : ITimestampable
{
    public long Id { get; set; }

    public required string Name { get; set; }

    public int StartingChannelNumber { get; set; }

    public required string DefaultLang { get; set; }
    
    public required DateTime CreatedAt { get; set; }
    
    public required DateTime UpdatedAt { get; set; }

    public virtual ICollection<PlaylistChannel> Channels { get; init; } = [];
}