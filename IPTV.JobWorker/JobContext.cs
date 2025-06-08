using System.Text.Json.Serialization;

namespace IPTV.JobWorker;

public class JobContext
{
    public Guid JobId { get; set; }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public JobType Type { get; set; }
}

public class JobContext<T> : JobContext
{
    public required T Options { get; set; }
}