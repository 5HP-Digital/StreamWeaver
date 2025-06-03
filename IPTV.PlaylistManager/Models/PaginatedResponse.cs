namespace IPTV.PlaylistManager.Models;

using System.Text.Json.Serialization;

public class PaginatedResponse<T>
{
    public int Page { get; set; }
    public int Total { get; set; }
    [JsonPropertyName("_links")]
    public PageLinks Links { get; set; } = new();
    public IEnumerable<T> Items { get; set; } = [];

    public class PageLinks
    {
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? First { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Last { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Next { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Previous { get; set; }
    }
}