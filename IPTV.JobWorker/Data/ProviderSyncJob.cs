namespace IPTV.JobWorker.Data;

public class ProviderSyncJob : Job
{
    public bool AllowStreamAutoDeletion { get; set; } = true;

    public virtual required Provider Provider { get; set; }
}