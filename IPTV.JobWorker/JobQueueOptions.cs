namespace IPTV.JobWorker;

public class JobQueueOptions
{
    public const int DefaultPollingInterval = 15; 
    
    public int PollingInterval { get; set; } = DefaultPollingInterval;
}