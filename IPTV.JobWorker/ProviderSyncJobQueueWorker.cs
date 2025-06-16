using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;
using Microsoft.EntityFrameworkCore;

namespace IPTV.JobWorker;

public class ProviderSyncJobQueueWorker(
    ILogger<ProviderSyncJobQueueWorker> logger, 
    IServiceProvider serviceProvider, 
    TimeProvider timeProvider) 
    : BackgroundService
{
    // TODO: interval from configuration
    private readonly PeriodicTimer _timer = new(TimeSpan.FromSeconds(15), timeProvider);
    
    public override async Task StartAsync(CancellationToken cancellationToken)
    {
        await base.StartAsync(cancellationToken);
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        logger.LogInformation("Provider sync worker starting");
        
        while (await _timer.WaitForNextTickAsync(cancellationToken: stoppingToken))
        {
            try
            {
                logger.LogInformation("Provider sync worker running at: {time}", timeProvider.GetUtcNow());

                await using var scope = serviceProvider.CreateAsyncScope();
                await using var workerContext = scope.ServiceProvider.GetRequiredService<WorkerContext>();

                var job = await workerContext.Jobs.Include(j => j.Provider)
                    .Where(j => j.State == JobState.Queued)
                    .OrderBy(j => j.CreatedAt)
                    .FirstOrDefaultAsync(cancellationToken: stoppingToken);

                if (job is null)
                {
                    logger.LogInformation("No queued jobs found");
                    continue;
                }

                try
                {
                    job.State = JobState.InProgress;
                    job.AttemptCount++;
                    job.LastAttemptStartedAt = timeProvider.GetUtcNow().DateTime;
                    job.StatusDescription =
                        $"Processing job (attempt {job.AttemptCount} of {job.MaxAttempts.ToString() ?? "Unlimited"})";
                    await workerContext.SaveChangesAsync(cancellationToken: stoppingToken);

                    logger.LogInformation("Processing job with ID {JobId} (attempt {AttemptCount} of {MaxAttempts})",
                        job.JobId, job.AttemptCount, job.MaxAttempts);

                    var start = timeProvider.GetTimestamp();
                    
                    var providerSynchronizer = scope.ServiceProvider.GetRequiredService<ProviderSynchronizer>();
                    var (success, description) = await providerSynchronizer.Run(job.Provider, job.AllowStreamAutoDeletion, cancellationToken: stoppingToken);

                    // retry on exception only, graceful unsuccessful processing fails the job
                    job.State = success ? JobState.Completed : JobState.Failed;
                    job.StatusDescription = description;
                    await workerContext.SaveChangesAsync(cancellationToken: stoppingToken);

                    var elapsed = timeProvider.GetElapsedTime(start);
                    
                    logger.LogInformation("Job with ID {JobId} processed in {Elapsed}", job.JobId, elapsed.ToString("G"));
                }
                catch (Exception ex)
                {
                    logger.LogError(ex, "Error processing job");

                    if (job.MaxAttempts is null || job.AttemptCount < job.MaxAttempts)
                    {
                        job.State = JobState.Queued;
                        job.StatusDescription =
                            $"Error processing job (attempt {job.AttemptCount} of {job.MaxAttempts.ToString() ?? "Unlimited"}). Queued for retry";
                    }
                    else
                    {
                        job.State = JobState.Failed;
                        job.StatusDescription =
                            $"Error processing job: {ex.Message}. Job will not be retried.";
                    }

                    await workerContext.SaveChangesAsync(cancellationToken: stoppingToken);
                }
            }
            catch (Exception ex)
            {
                // prevent the worker from crashing if there's an error processing a job
                logger.LogCritical(ex, "Unexpected error processing job");
            }
        }
        
        logger.LogInformation("Provider sync worker stopping");
    }
    
    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        _timer.Dispose();
        
        await base.StopAsync(cancellationToken);
    }
}