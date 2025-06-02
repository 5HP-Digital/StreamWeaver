namespace IPTV.PlaylistManager.Data;

public class PlaylistSource : IEntity
{
    public long Id { get; init; }
    
    public required string Name { get; set; }
    
    public required string Url { get; set; }
    
    public DateTime CreatedAt { get; set; }
    
    public DateTime UpdatedAt { get; set; }
    
    public ICollection<PlaylistSourceInvocation> Invocations { get; init; } = [];
}