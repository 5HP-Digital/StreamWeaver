namespace IPTV.JobWorker.Data;

public class Guide
{
    public long Id { get; set; }

    public required string Site { get; set; }

    public required string SiteId { get; set; }
    
    public required string SiteName { get; set; }
    
    public required string Lang { get; set; }

    public string? XmltvId { get; set; }

    public virtual ICollection<PlaylistChannel> PlaylistChannels { get; init; } = [];
}