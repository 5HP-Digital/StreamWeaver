using IPTV.JobWorker;
using IPTV.JobWorker.Data;
using IPTV.JobWorker.Services;
using RabbitMQ.Client;

var builder = Host.CreateApplicationBuilder(args);

// Sqlite
builder.Services.AddDbContext<WorkerContext>();

// RabbitMQ
builder.Services.AddSingleton<IConnectionFactory>(sp => new ConnectionFactory
{
    HostName = builder.Configuration["RABBITMQ_HOST"] ?? "localhost",
    Port = builder.Configuration.GetValue<int?>("RABBITMQ_PORT") ?? 5672,
    UserName = builder.Configuration["RABBITMQ_USER"] ?? "guest",
    Password = builder.Configuration["RABBITMQ_PWD"] ?? "guest"
});

builder.Services.AddScoped<PlaylistSynchronizer>();
builder.Services.AddHostedService<PlaylistSyncJobQueueWorker>();

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