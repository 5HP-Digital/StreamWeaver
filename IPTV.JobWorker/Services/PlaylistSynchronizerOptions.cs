namespace IPTV.JobWorker.Services;

public class PlaylistSynchronizerOptions
{
    public required long SourceId { get; set; }

    public required bool AllowChannelAutoDeletion { get; set; }
}