namespace IPTV.PlaylistManager.Data;

public interface IEntity
{
    DateTime CreatedAt { get; set; }
    
    DateTime UpdatedAt { get; set; }
}