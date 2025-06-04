namespace IPTV.PlaylistManager.Data;

public class PlaylistSource : IEntity
{
    public long Id { get; init; }
    
    public required string Name { get; set; }
    
    public required string Url { get; set; }
    
    public bool IsEnabled { get; set; } = false;
    
    public DateTime CreatedAt { get; set; }
    
    public DateTime UpdatedAt { get; set; }
    
    // Navigation properties
    public ICollection<PlaylistSourceChannel> Channels { get; init; } = [];
    public ICollection<PlaylistSourceInvocation> Invocations { get; init; } = [];
}