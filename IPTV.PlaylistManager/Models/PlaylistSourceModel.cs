namespace IPTV.PlaylistManager.Models;

public class PlaylistSourceModel
{
    public long Id { get; init; }
    
    public required string Name { get; init; }
    
    public required string Url { get; init; }
    
    public DateTime CreatedAt { get; init; }
    
    public DateTime UpdatedAt { get; init; }
}