using IPTV.JobWorker;
using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;

var builder = Host.CreateApplicationBuilder(args);

builder.Services.AddDbContext<WorkerContext>();

builder.Services.AddScoped<PlaylistSynchronizer>();
builder.Services.AddHostedService<JobQueueWorker>();

builder.Services.AddHttpClient(nameof(PlaylistSynchronizer),
    client =>
    {
        client.Timeout = TimeSpan.FromMinutes(5);
        client.MaxResponseContentBufferSize = 256 * 1024 * 1024;
        client.DefaultRequestHeaders.Clear();
    })
    .SetHandlerLifetime(TimeSpan.FromMinutes(5));

var host = builder.Build();

host.Run();