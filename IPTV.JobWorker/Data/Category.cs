namespace IPTV.JobWorker.Data;

public class Category
{
    public long Id { get; set; }

    public required string Code { get; set; }

    public required string Name { get; set; }
}