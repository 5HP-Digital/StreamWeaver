using dotenv.net;
using IPTV.JobWorker;
using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;

DotEnv.Load();

var builder = Host.CreateApplicationBuilder(args);

builder.Services.AddSingleton(TimeProvider.System);

// Sqlite
builder.Services.AddDbContext<WorkerContext>();

builder.Services.AddScoped<ProviderSynchronizer>();
builder.Services.AddHostedService<ProviderSyncJobQueueWorker>();

builder.Services.AddHttpClient(nameof(ProviderSynchronizer),
    client =>
    {
        client.Timeout = TimeSpan.FromMinutes(5);
        client.MaxResponseContentBufferSize = 256 * 1024 * 1024;
        client.DefaultRequestHeaders.Clear();
    })
    .SetHandlerLifetime(TimeSpan.FromMinutes(5));

var host = builder.Build();

host.Run();