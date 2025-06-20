using System.Collections.Immutable;
using Digital5HP.Text.M3U;
using EFCore.BulkExtensions;
using IPTV.JobWorker.Data;
using Microsoft.EntityFrameworkCore;

namespace IPTV.JobWorker.Services;

public class ProviderSynchronizer(
    WorkerContext workerContext, 
    IHttpClientFactory httpClientFactory, 
    TimeProvider timeProvider,
    ILogger<ProviderSynchronizer> logger)
{
    public async Task<(bool, string?)> Run(Provider provider, bool allowStreamAutoDeletion, CancellationToken cancellationToken)
    {
        if (!provider.IsEnabled)
        {
            logger.LogWarning("Provider with ID {ProviderId} is not enabled", provider.Id);
            
            return (false, "Service provider is not enabled");
        }

        var client = httpClientFactory.CreateClient(nameof(ProviderSynchronizer));

        // Retrieve and deserialize m3u file
        Document document;
        await using (var stream = await client.GetStreamAsync(provider.Url, cancellationToken))
        {
            document = await Serializer.DeserializeAsync(stream, cancellationToken);
        }
        
        logger.LogInformation("Document with {StreamCount} streams retrieved from {ProviderUrl}", document.Channels.Count, provider.Url);
        
        var streams = await workerContext.Streams.AsNoTracking()
            .Include(s => s.Provider)
            .Where(s => s.Provider == provider)
            .ToListAsync(cancellationToken: cancellationToken);
        
        // Index existing streams for the provider, avoid duplicates
        var existingStreams = streams.GroupBy(s => (s.Title, s.Group))
            .ToImmutableDictionary(s => (s.Key.Title, s.Key.Group), g => g.First());
        
        logger.LogInformation("Indexed {StreamCount} existing streams", streams.Count);

        await using var transaction = await workerContext.Database.BeginTransactionAsync(cancellationToken);
        
        // Sync streams
        var streamsToAdd = new List<ProviderStream>();
        var streamsToUpdate = new List<ProviderStream>();
        foreach (var channel in document.Channels)
        {
            // Skip streams without a title or media URL
            if (string.IsNullOrWhiteSpace(channel.Title) || string.IsNullOrWhiteSpace(channel.MediaUrl))
                continue;
            
            // Check if the stream already exists
            if (existingStreams.TryGetValue((channel.Title, channel.GroupTitle), out var stream))
            {
                // Update existing stream
                stream.Title = channel.Title;
                stream.TvgId = channel.TvgId;
                stream.MediaUrl = channel.MediaUrl;
                stream.LogoUrl = channel.LogoUrl;
                stream.Group = channel.GroupTitle;
                stream.IsActive = true;
                stream.UpdatedAt = timeProvider.GetUtcNow().DateTime;
                
                streamsToUpdate.Add(stream);
            }
            else
            {
                // Create a new stream
                streamsToAdd.Add(new ProviderStream
                {
                    Title = channel.Title,
                    TvgId = channel.TvgId,
                    MediaUrl = channel.MediaUrl,
                    LogoUrl = channel.LogoUrl,
                    Group = channel.GroupTitle,
                    IsActive = true,
                    Provider = provider,
                    CreatedAt = timeProvider.GetUtcNow().DateTime,
                    UpdatedAt = timeProvider.GetUtcNow().DateTime
                });
            }
        }
        
        // Handle streams that weren't in the m3u file
        var validStreams = document.Channels.Select(c => (c.Title, (string?)c.GroupTitle)).ToHashSet();
        var streamsToRemove = streams.Where(s => !validStreams.Contains((s.Title, s.Group))).ToList();
            
        // Save changes
        await workerContext.BulkInsertAsync(streamsToAdd, cancellationToken: cancellationToken);
        await workerContext.BulkUpdateAsync(streamsToUpdate, cancellationToken: cancellationToken);
        
        if (allowStreamAutoDeletion)
        {
            await workerContext.BulkDeleteAsync(streamsToRemove, cancellationToken: cancellationToken);
        }
        else
        {
            var now = timeProvider.GetUtcNow().DateTime;
            streamsToRemove.ForEach(stream =>
            {
                stream.IsActive = false;
                stream.UpdatedAt = now;
            });
            await workerContext.BulkUpdateAsync(streamsToRemove, cancellationToken: cancellationToken);
        }
        
        await transaction.CommitAsync(cancellationToken);

        logger.LogInformation("Streams synced ({Added} added;{Updated} updated;{Removed} removed)", 
            streamsToAdd.Count, streamsToUpdate.Count, streamsToRemove.Count);
        
        return (true, $"Synced {streamsToAdd.Count + streamsToUpdate.Count} streams");
    }
}