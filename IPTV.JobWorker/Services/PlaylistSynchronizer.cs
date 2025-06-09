using System.Collections;
using System.Collections.Specialized;
using Digital5HP.Text.M3U;
using IPTV.JobWorker.Data;

namespace IPTV.JobWorker.Services;

public class PlaylistSynchronizer(
    WorkerContext workerContext, 
    IHttpClientFactory httpClientFactory, 
    ILogger<PlaylistSynchronizer> logger) 
    : IJobRunner<PlaylistSynchronizerOptions>
{
    public async Task Run(PlaylistSynchronizerOptions options, CancellationToken cancellationToken)
    {
        // Retrieve PlaylistSource
        
        // ReSharper disable once EntityFramework.NPlusOne.IncompleteDataQuery
        var source = await workerContext.PlaylistSources.FindAsync([options.SourceId], cancellationToken: cancellationToken);

        // Validate PlaylistSource
        if (source == null)
        {
            logger.LogError("PlaylistSource with ID {SourceId} was not found", options.SourceId);
            return;
        }

        if (!source.IsEnabled)
        {
            logger.LogWarning("PlaylistSource with ID {SourceId} is not enabled", options.SourceId);
            return;
        }

        var client = httpClientFactory.CreateClient(nameof(PlaylistSynchronizer));

        // Retrieve and deserialize playlist
        Document document;
        await using (var stream = await client.GetStreamAsync(source.Url, cancellationToken))
        {
            document = await Serializer.DeserializeAsync(stream, cancellationToken);
        }

        // Index existing channels for the playlist source
        // ReSharper disable once EntityFramework.NPlusOne.IncompleteDataUsage
        var existingChannels = new HybridDictionary(source.Channels.Count);
        // ReSharper disable once EntityFramework.NPlusOne.IncompleteDataUsage
        foreach (var channel in source.Channels)
        {
            existingChannels.Add((channel.Title, channel.Group), channel);
        }
        
        // Track which channels were processed
        var processedChannels = new HashSet<(string Title, string? Group)>();
        
        // Sync channels
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
            }
            
            // Mark as processed
            processedChannels.Add(key);
        }
        
        // Handle channels that weren't in the m3u file
        foreach (var channel in from DictionaryEntry entry in existingChannels 
                 let key = ((string Title, string? Group))entry.Key 
                 let channel = (PlaylistSourceChannel)entry.Value! 
                 where !processedChannels.Contains(key) 
                 select channel)
        {
            if (options.AllowChannelAutoDeletion)
            {
                // Delete channel
                source.Channels.Remove(channel);
            }
            else
            {
                // Mark as inactive
                channel.IsActive = false;
            }
        }
        
        // Save changes
        await workerContext.SaveChangesAsync(cancellationToken: cancellationToken);
    }
}