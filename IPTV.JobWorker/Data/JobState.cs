namespace IPTV.JobWorker.Data;

public enum JobState
{
    Queued,
    InProgress,
    Completed,
    Failed
}