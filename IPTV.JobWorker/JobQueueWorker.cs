using System.Text;
using System.Text.Json;
using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;
using Microsoft.EntityFrameworkCore;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using TimeProvider = Digital5HP.TimeProvider;

namespace IPTV.JobWorker;

public class JobQueueWorker(ILogger<JobQueueWorker> logger, IServiceProvider serviceProvider, ConnectionFactory connectionFactory) : BackgroundService
{
    private IConnection? _connection;
    private IChannel? _channel;
    private const string QueueName = "jobs_queue";
    private const int MaxAttempts = 3;

    public override async Task StartAsync(CancellationToken cancellationToken)
    {
        _connection = await connectionFactory.CreateConnectionAsync(cancellationToken);
        _channel = await _connection.CreateChannelAsync(cancellationToken: cancellationToken);
        
        await _channel.QueueDeclareAsync(
            queue: QueueName,
            durable: true,
            exclusive: false,
            autoDelete: false,
            arguments: null,
            cancellationToken: cancellationToken);
        
        logger.LogInformation("RabbitMQ connection established and queue declared at: {time}", TimeProvider.Current.Now);
        
        await base.StartAsync(cancellationToken);
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var consumer = new AsyncEventingBasicConsumer(_channel!);
        
        consumer.ReceivedAsync += async (_, ea) =>
        {
            try
            {
                var body = ea.Body.ToArray();
                var message = Encoding.UTF8.GetString(body);
                
                logger.LogInformation("Received message: {message}", message);
                
                var jobContext = JsonSerializer.Deserialize<JobContext>(message);
                
                if (jobContext == null)
                {
                    logger.LogError("Failed to deserialize message into JobContext");
                    await _channel!.BasicNackAsync(ea.DeliveryTag, false, false, cancellationToken: stoppingToken);
                    return;
                }

                await ProcessJobAsync(jobContext, message, stoppingToken);
                
                await _channel!.BasicAckAsync(ea.DeliveryTag, false, cancellationToken: stoppingToken);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error processing message");
                await _channel!.BasicNackAsync(ea.DeliveryTag, false, true, cancellationToken: stoppingToken);
            }
        };
        
        await _channel!.BasicConsumeAsync(
            queue: QueueName,
            autoAck: false,
            consumer: consumer,
            cancellationToken: stoppingToken);
        
        // Keep the service running until cancellation is requested
        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(1000, stoppingToken);
        }
    }
    
    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        if (_channel != null) await _channel.CloseAsync(cancellationToken);
        if (_connection != null) await _connection.CloseAsync(cancellationToken);
        if (_channel != null) await _channel.DisposeAsync();
        if (_connection != null) await _connection.DisposeAsync();
        
        await base.StopAsync(cancellationToken);
    }
    
    private async Task ProcessJobAsync(JobContext jobContext, string message, CancellationToken cancellationToken)
    {
        logger.LogInformation("Processing job of type {JobType} with ID {JobId}", 
            jobContext.Type, jobContext.JobId);
        
        await using var workerContext = serviceProvider.GetRequiredService<WorkerContext>();
        
        var job = await workerContext.Jobs.SingleOrDefaultAsync(j => j.JobId == jobContext.JobId, cancellationToken: cancellationToken);
        if (job == null)
        {
            logger.LogError("Job with ID {JobId} was not found", jobContext.JobId);
            return;
        }

        if (job.State != JobState.Pending)
        {
            logger.LogError("Job with ID {JobId} is not in Pending state", jobContext.JobId);
            return;
        }
        
        job.State = JobState.InProgress;
        job.AttemptCount++;
        await workerContext.SaveChangesAsync(cancellationToken: cancellationToken);

        try
        {
            switch (jobContext.Type)
            {
                case JobType.PlaylistSync:
                    await RunJob<PlaylistSynchronizer, PlaylistSynchronizerOptions>(message, cancellationToken);
                    break;

                default:
                    logger.LogWarning("Unknown job type: {JobType}", jobContext.Type);
                    
                    job.State = JobState.Failed;
                    job.Error = $"Unknown job type: {jobContext.Type}";
                    return;
            }
            
            job.State = JobState.Completed;
            job.Error = null;
        }
        catch (Exception ex)
        {
            job.Error = $"Failed to run job: {ex.Message}";

            if (job.AttemptCount < MaxAttempts)
            {
                // Retry the job
                job.State = JobState.Pending;
                
                throw;
            }
            else
            {
                // Last attempt failed, mark job as failed
                job.State = JobState.Failed;
            }
        }
        finally
        {
            await workerContext.SaveChangesAsync(cancellationToken: cancellationToken);
        }
    }

    private async Task RunJob<T, TOption>(string message, CancellationToken cancellationToken)
        where T : IJobRunner<TOption>
    {
        var jc = JsonSerializer.Deserialize<JobContext<TOption>>(message);
        if (jc == null)
        {
            logger.LogError("Failed to deserialize job options");
            return;
        }

        using var scope = serviceProvider.CreateScope();
        
        var runner = scope.ServiceProvider.GetRequiredService<T>();
        await runner.Run(jc.Options, cancellationToken);
    }
}