namespace IPTV.PlaylistManager.Models;

using System.ComponentModel.DataAnnotations;

public class PlaylistSourceUpdateModel
{
    [MaxLength(100)]
    public string? Name { get; set; }
    
    [MaxLength(500)]
    [Url]
    public string? Url { get; set; }
    
    public bool? IsEnabled { get; set; }
}