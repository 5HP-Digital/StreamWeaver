namespace IPTV.JobWorker.Data;

public class PlaylistEpgGenJob : Job
{
    public virtual required Playlist Playlist { get; set; }
}