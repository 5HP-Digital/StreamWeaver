using System.Collections;
using System.Collections.Specialized;
using Digital5HP.Text.M3U;
using IPTV.JobWorker.Data;

namespace IPTV.JobWorker.Services;

public class ProviderSynchronizer(
    WorkerContext workerContext, 
    IHttpClientFactory httpClientFactory, 
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
        
        // Index existing streams for the provider
        var existingStreams = new HybridDictionary(provider.Streams.Count);
        foreach (var stream in provider.Streams)
        {
            existingStreams.Add((stream.Title, stream.Group), stream);
        }
        
        logger.LogInformation("{StreamCount} existing streams indexed", provider.Streams.Count);
        
        // Track which streams were processed
        var processedStreams = new HashSet<(string Title, string? Group)>();
        
        // Sync streams
        var added = 0;
        var updated = 0;
        foreach (var channel in document.Channels)
        {
            var key = (channel.Title, channel.GroupTitle);
            
            // Skip streams without a title or media URL
            if (string.IsNullOrWhiteSpace(channel.Title) || string.IsNullOrWhiteSpace(channel.MediaUrl))
                continue;
            
            // Skip duplicate streams
            // Currently, we don't support multiple streams with the same title and group
            if (processedStreams.Contains(key))
                continue;
            
            // Check if the stream already exists
            if (existingStreams.Contains(key))
            {
                // Update existing stream
                var streamToUpdate = (ProviderStream)existingStreams[key]!;
                streamToUpdate.Title = channel.Title;
                streamToUpdate.TvgId = channel.TvgId;
                streamToUpdate.MediaUrl = channel.MediaUrl;
                streamToUpdate.LogoUrl = channel.LogoUrl;
                streamToUpdate.Group = channel.GroupTitle;
                streamToUpdate.IsActive = true;
                
                updated++;
            }
            else
            {
                // Create a new stream
                provider.Streams.Add(new ProviderStream
                {
                    Title = channel.Title,
                    TvgId = channel.TvgId,
                    MediaUrl = channel.MediaUrl,
                    LogoUrl = channel.LogoUrl,
                    Group = channel.GroupTitle,
                    IsActive = true,
                });

                added++;
            }
            
            // Mark as processed
            processedStreams.Add(key);
        }
        
        logger.LogInformation("{Updated} streams updated; {Added} streams added", updated, added);
        
        // Handle streams that weren't in the m3u file
        var deleted = 0;
        foreach (var stream in from DictionaryEntry entry in existingStreams 
                 let key = ((string Title, string? Group))entry.Key 
                 let stream = (ProviderStream)entry.Value! 
                 where !processedStreams.Contains(key) 
                 select stream)
        {
            if (allowStreamAutoDeletion)
            {
                // Delete stream
                provider.Streams.Remove(stream);
            }
            else
            {
                // Mark as inactive
                stream.IsActive = false;
            }
            
            deleted++;
        }
        
        logger.LogInformation("{Deleted} streams deleted", deleted);
        
        // Save changes
        await workerContext.SaveChangesAsync(cancellationToken: cancellationToken);
        
        return (true, $"Service provider streams synced: {added} added; {updated} updated; {deleted} deleted");
    }
}