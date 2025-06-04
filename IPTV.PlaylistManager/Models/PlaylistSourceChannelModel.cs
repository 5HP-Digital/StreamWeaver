namespace IPTV.PlaylistManager.Models;

public class PlaylistSourceChannelModel
{
    public long Id { get; set; }
    public string Title { get; set; } = null!;
    public string? TvgId { get; set; }
    public string MediaUrl { get; set; } = null!;
    public string? LogoUrl { get; set; }
    public string? Group { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}