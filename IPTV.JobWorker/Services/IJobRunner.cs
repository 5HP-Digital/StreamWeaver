namespace IPTV.JobWorker.Services;

public interface IJobRunner<in T>
{
    Task Run(T options, CancellationToken cancellationToken);
}