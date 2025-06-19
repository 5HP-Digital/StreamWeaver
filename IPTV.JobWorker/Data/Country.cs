namespace IPTV.JobWorker.Data;

public class Country
{
    public long Id { get; set; }

    public required string Code { get; set; }

    public required string Name { get; set; }

    public string? Flag { get; set; }
}