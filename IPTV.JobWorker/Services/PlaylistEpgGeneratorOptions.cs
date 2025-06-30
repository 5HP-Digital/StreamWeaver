namespace IPTV.JobWorker.Services;

public class PlaylistEpgGeneratorOptions
{
    public const string DefaultEpgServiceBaseUrl = "http://localhost:3000";
    
    public required string EpgServiceBaseUrl { get; set; }
}