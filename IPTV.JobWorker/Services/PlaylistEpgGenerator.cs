using System.Text;
using System.Xml;
using System.Xml.Linq;
using Digital5HP;
using IPTV.JobWorker.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using TimeProvider = System.TimeProvider;

namespace IPTV.JobWorker.Services;

public class PlaylistEpgGenerator(
    WorkerContext workerContext,
    IHttpClientFactory httpClientFactory,
    IOptions<PlaylistEpgGeneratorOptions> options,
    ILogger<ProviderSynchronizer> logger)
{
    public async Task<(bool, string?)> Run(Playlist playlist, CancellationToken cancellationToken)
    {
        try
        {
            // Retrieve guides from the playlist provided 
            var guides = await workerContext.Guides.AsNoTracking()
                .Where(g => g.PlaylistChannels.Any(pc => pc.Playlist == playlist))
                .ToListAsync(cancellationToken);

            var xml = CreateXml(guides);

            var httpClient = httpClientFactory.CreateClient(nameof(PlaylistEpgGenerator));

            var content = new StringContent(
                xml,
                Encoding.UTF8,
                "application/xml");

            var generatorOptions = options.Value;
            var path =
                new Uri(generatorOptions.EpgServiceBaseUrl).Combine(
                    $"generate-guide/{playlist.Id}"); // throws if not valid ("http://localhost:5000/generate-guide/123")
            var response = await httpClient.PostAsync(path, content, cancellationToken);

            return response.IsSuccessStatusCode
                ? (true, "Guide generated successfully")
                : (false, $"Failed to generate guide: {await response.Content.ReadAsStringAsync(cancellationToken)}");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error generating guide");
            return (false, $"Error generating guide: {ex.Message}");
        }
    }
    
    private static string CreateXml(IEnumerable<Guide> guides)
    {
        // Convert guides to Channel XML
        var channelsElement = new XElement(
            "channels",
            from g in guides
            select new XElement(
                "channel",
                new XAttribute("site", g.Site),
                new XAttribute("lang", g.Lang),
                new XAttribute("xmltv_id", g.XmltvId),
                new XAttribute("site_id", g.SiteId))
            {
                Value = g.SiteName
            }
        );

        var document = new XDocument(channelsElement)
        {
            Declaration = new XDeclaration("1.0", "utf-8", null),
        };

        using var memoryStream = new MemoryStream();
        using (var xmlWriter =
               XmlWriter.Create(memoryStream,
                   new XmlWriterSettings { OmitXmlDeclaration = false, Encoding = Encoding.UTF8 }))
        {
            document.WriteTo(xmlWriter);
            xmlWriter.Flush();
        }
                
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream, Encoding.UTF8);
        return reader.ReadToEnd();
    }
}