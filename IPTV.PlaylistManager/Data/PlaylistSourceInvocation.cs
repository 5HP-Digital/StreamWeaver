namespace IPTV.PlaylistManager.Data;

public class PlaylistSourceInvocation : IEntity
{
    public long Id { get; set; }
    
    public string? Error { get; set; }
    
    public DateTime CreatedAt { get; set; }
    
    public DateTime UpdatedAt { get; set; }
}