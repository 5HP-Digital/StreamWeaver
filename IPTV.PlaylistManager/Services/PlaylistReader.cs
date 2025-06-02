namespace IPTV.PlaylistManager.Services;

using Digital5HP.Text.M3U;

public class PlaylistReader(HttpClient httpClient)
{
    public async Task<Document> ReadAsync(string m3uUrl, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(m3uUrl))
            throw new ArgumentException("M3U URL cannot be null or empty", nameof(m3uUrl));

        try
        {
            await using var response = await httpClient.GetStreamAsync(m3uUrl, cancellationToken);
            
            return await Serializer.DeserializeAsync(response, cancellationToken);
        }
        catch (HttpRequestException ex)
        {
            throw new PlaylistException($"Failed to download M3U playlist from {m3uUrl}", ex);
        }
        catch (SerializationException ex)
        {
            throw new PlaylistException($"Failed to parse M3U playlist from {m3uUrl}", ex);
        }
    }
}