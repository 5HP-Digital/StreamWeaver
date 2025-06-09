using System.Collections;
using System.Collections.Specialized;
using Digital5HP.Text.M3U;
using IPTV.JobWorker.Data;

namespace IPTV.JobWorker.Services;

public class PlaylistSynchronizer(
    WorkerContext workerContext, 
    IHttpClientFactory httpClientFactory, 
    ILogger<PlaylistSynchronizer> logger)
{
    public async Task<(bool, string?)> Run(PlaylistSource source, bool allowChannelAutoDeletion, CancellationToken cancellationToken)
    {
        if (!source.IsEnabled)
        {
            logger.LogWarning("PlaylistSource with ID {SourceId} is not enabled", source.Id);
            
            return (false, "Service provider is not enabled");
        }

        var client = httpClientFactory.CreateClient(nameof(PlaylistSynchronizer));

        // Retrieve and deserialize playlist
        Document document;
        await using (var stream = await client.GetStreamAsync(source.Url, cancellationToken))
        {
            document = await Serializer.DeserializeAsync(stream, cancellationToken);
        }
        
        logger.LogInformation("Playlist with {ChannelCount} channels retrieved from {SourceUrl}", document.Channels.Count, source.Url);
        
        // Index existing channels for the playlist source)
        var existingChannels = new HybridDictionary(source.Channels.Count);
        foreach (var channel in source.Channels)
        {
            existingChannels.Add((channel.Title, channel.Group), channel);
        }
        
        logger.LogInformation("{ChannelCount} existing channels indexed", source.Channels.Count);
        
        // Track which channels were processed
        var processedChannels = new HashSet<(string Title, string? Group)>();
        
        // Sync channels
        var added = 0;
        var updated = 0;
        foreach (var channel in document.Channels)
        {
            var key = (channel.Title, channel.GroupTitle);
            
            // Skip channels without a title or media URL
            if (string.IsNullOrWhiteSpace(channel.Title) || string.IsNullOrWhiteSpace(channel.MediaUrl))
                continue;
            
            // Skip duplicate channels
            // Currently, we don't support multiple channels with the same title and group
            if (processedChannels.Contains(key))
                continue;
            
            // Check if the channel already exists
            if (existingChannels.Contains(key))
            {
                // Update existing channel
                var channelToUpdate = (PlaylistSourceChannel)existingChannels[key]!;
                channelToUpdate.Title = channel.Title;
                channelToUpdate.TvgId = channel.TvgId;
                channelToUpdate.MediaUrl = channel.MediaUrl;
                channelToUpdate.LogoUrl = channel.LogoUrl;
                channelToUpdate.Group = channel.GroupTitle;
                channelToUpdate.IsActive = true;
                
                updated++;
            }
            else
            {
                // Create a new channel
                source.Channels.Add(new PlaylistSourceChannel
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
            processedChannels.Add(key);
        }
        
        logger.LogInformation("{Updated} channels updated; {Added} channels added", updated, added);
        
        // Handle channels that weren't in the m3u file
        var deleted = 0;
        foreach (var channel in from DictionaryEntry entry in existingChannels 
                 let key = ((string Title, string? Group))entry.Key 
                 let channel = (PlaylistSourceChannel)entry.Value! 
                 where !processedChannels.Contains(key) 
                 select channel)
        {
            if (allowChannelAutoDeletion)
            {
                // Delete channel
                source.Channels.Remove(channel);
            }
            else
            {
                // Mark as inactive
                channel.IsActive = false;
            }
            
            deleted++;
        }
        
        logger.LogInformation("{Deleted} channels deleted", deleted);
        
        // Save changes
        await workerContext.SaveChangesAsync(cancellationToken: cancellationToken);
        
        return (true, $"Service provider channels synced: {added} added; {updated} updated; {deleted} deleted");
    }
}