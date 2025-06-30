namespace IPTV.JobWorker.Data;

public class PlaylistChannel : ITimestampable
{
    public long Id { get; set; }
    
    public string? Title { get; set; }

    public string? LogoUrl { get; set; }

    public string? Category { get; set; }

    public required int Order { get; set; }
    
    public required DateTime CreatedAt { get; set; }
    
    public required DateTime UpdatedAt { get; set; }
    
    public virtual Guide? Guide { get; set; }
    
    public virtual required ProviderStream Stream { get; set; }

    public virtual required Playlist Playlist { get; set; }
}