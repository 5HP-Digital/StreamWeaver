namespace IPTV.JobWorker.Data;

public class ProviderChannel : ITimestampable
{
    public long Id { get; set; }
    public required string Title { get; set; }
    public string? TvgId { get; set; }
    public required string MediaUrl { get; set; }
    public string? LogoUrl { get; set; }
    public string? Group { get; set; }
    public bool IsActive{ get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
