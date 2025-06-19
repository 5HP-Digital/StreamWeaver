namespace IPTV.JobWorker.Data;

public class Channel
{
    public long Id { get; set; }

    public required string XmltvId { get; set; }

    public required string Name { get; set; }

    public string? Network { get; set; }

    public required string Country { get; set; }

    public string? City { get; set; }

    public string[] Categories { get; set; } = [];

    public required bool IsNsfw { get; set; } = false;

    public DateOnly? LaunchedAt { get; set; }
    
    public DateOnly? ClosedAt { get; set; }
    
    public string? WebsiteUrl { get; set; }
    
    public string? LogoUrl { get; set; }
}