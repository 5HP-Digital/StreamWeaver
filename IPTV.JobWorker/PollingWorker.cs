using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace IPTV.JobWorker;

public class PollingWorker(
    ILogger<PollingWorker> logger,
    IServiceProvider serviceProvider, 
    TimeProvider timeProvider,
    IOptions<JobQueueOptions> options) 
    : BackgroundService
{
    private const int AbsoluteMaxAttempts = 100;
    
    private readonly PeriodicTimer _timer = new(TimeSpan.FromSeconds(options.Value.PollingInterval), timeProvider);
    
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

                await Poll(stoppingToken);
            }
            catch (OperationCanceledException)
            {
                // prevent the worker from crashing if the operation is canceled
            }
            catch (Exception ex)
            {
                // prevent the worker from crashing if there's an error processing a job
                logger.LogCritical(ex, "Unexpected error processing job");
            }
        }
        
        logger.LogInformation("Provider sync worker stopping");
    }

    private async Task Poll(CancellationToken stoppingToken)
    {
        await using var scope = serviceProvider.CreateAsyncScope();
        await using var workerContext = scope.ServiceProvider.GetRequiredService<WorkerContext>();

        var job = await workerContext.Jobs.Where(j => j.State == JobState.Queued)
            .OrderBy(j => j.CreatedAt)
            .FirstOrDefaultAsync(cancellationToken: stoppingToken);

        if (job is null)
        {
            logger.LogInformation("No queued jobs found");
            return;
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

            bool success;
            string? description;
                    
            // process job
            switch (job.Type)
            {
                case JobType.ProviderSync:
                    var providerSyncJob = (ProviderSyncJob)job;
                    var providerSynchronizer = scope.ServiceProvider.GetRequiredService<ProviderSynchronizer>();
                    (success, description) = await providerSynchronizer.Run(providerSyncJob.Provider,
                        providerSyncJob.AllowStreamAutoDeletion, cancellationToken: stoppingToken);
                    break;
                case JobType.EpgDataSync:
                    var epgOrgDataSynchronizer = scope.ServiceProvider.GetRequiredService<EpgOrgDataSynchronizer>();
                    (success, description) = await epgOrgDataSynchronizer.Run(cancellationToken: stoppingToken);
                    break;
                default:
                    throw new NotSupportedException($"Unsupported job type: {job.Type}");
            }

            // retry on exception only, graceful unsuccessful processing fails the job
            job.State = success ? JobState.Completed : JobState.Failed;
            job.StatusDescription = description;
            await workerContext.SaveChangesAsync(cancellationToken: stoppingToken);

            var elapsed = timeProvider.GetElapsedTime(start);

            logger.LogInformation("Job with ID {JobId} processed in {Elapsed}", job.JobId,
                elapsed.ToString("G"));
        }
        catch (OperationCanceledException)
        {
            // prevent the worker from crashing if the operation is canceled
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error processing job");

            if (job.AttemptCount < (job.MaxAttempts ?? AbsoluteMaxAttempts))
            {
                job.State = JobState.Queued;
                job.StatusDescription =
                    $"Error processing job (attempt {job.AttemptCount} of {job.MaxAttempts ?? AbsoluteMaxAttempts}). Queued for retry";
            }
            else
            {
                job.State = JobState.Failed;
                job.StatusDescription =
                    $"Error processing job: {ex.Message.TrimEnd('.')}. Last attempt reached.";
            }

            await workerContext.SaveChangesAsync(cancellationToken: stoppingToken);
        }
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        _timer.Dispose();
        
        await base.StopAsync(cancellationToken);
    }
}