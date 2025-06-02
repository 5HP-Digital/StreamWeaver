namespace IPTV.PlaylistManager.Models;

using System.ComponentModel.DataAnnotations;

public class PlaylistSourceUpdateModel
{
    [Required]
    [MaxLength(100)]
    public required string Name { get; set; }
    
    [Required]
    [MaxLength(500)]
    [Url]
    public required string Url { get; set; }
}