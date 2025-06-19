using dotenv.net;
using IPTV.JobWorker;
using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;

DotEnv.Load();

var builder = Host.CreateApplicationBuilder(args);

builder.Services.AddSingleton(TimeProvider.System);

// Options
builder.Services.AddOptions<JobQueueOptions>()
    .Configure(options =>
        options.PollingInterval =
            builder.Configuration.GetValue("JOB_QUEUE_POLLING_INTERVAL", JobQueueOptions.DefaultPollingInterval));

// Sqlite
builder.Services.AddDbContext<WorkerContext>();

// Job runners
builder.Services.AddScoped<EpgOrgDataSynchronizer>();
builder.Services.AddScoped<ProviderSynchronizer>();

// Background worker
builder.Services.AddHostedService<PollingWorker>();

// HttpClient
builder.Services.AddHttpClient(nameof(EpgOrgDataSynchronizer),
    client =>
    {
        client.Timeout = TimeSpan.FromSeconds(30);
        client.MaxResponseContentBufferSize = 32 * 1024 * 1024;
        client.DefaultRequestHeaders.Clear();
    })
    .SetHandlerLifetime(TimeSpan.FromSeconds(30));
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