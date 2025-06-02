using Microsoft.EntityFrameworkCore;

using IPTV.PlaylistManager.Data;
using IPTV.PlaylistManager.Services;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Extensions.Diagnostics.HealthChecks;

var builder = WebApplication.CreateSlimBuilder(args);

builder.Services.AddHttpClient(
        nameof(PlaylistReader),
        client =>
        {
            client.Timeout = TimeSpan.FromMinutes(5);
            client.MaxResponseContentBufferSize = 256 * 1024 * 1024;
            client.DefaultRequestHeaders.Clear();
        })
    .SetHandlerLifetime(TimeSpan.FromMinutes(5));
builder.Services.AddScoped<PlaylistReader>();

// Add database configuration
var connectionString = $"Host={Environment.GetEnvironmentVariable("POSTGRES_HOST")};" +
                       $"Database={Environment.GetEnvironmentVariable("POSTGRES_DB")};" +
                       $"Username={Environment.GetEnvironmentVariable("POSTGRES_USER")};" +
                       $"Password={Environment.GetEnvironmentVariable("POSTGRES_PASSWORD")};" +
                       $"Port={Environment.GetEnvironmentVariable("POSTGRES_PORT")}";

builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseNpgsql(connectionString);
});

// Add health checks
builder.Services.AddHealthChecks()
    .AddNpgSql(connectionString, 
        name: "database", 
        failureStatus: HealthStatus.Unhealthy, 
        tags: ["db"])
    .AddCheck(name: "api", 
        check: () => HealthCheckResult.Healthy("API is responsive"), 
        tags: ["api"]);

// Add controllers
builder.Services.AddControllers();

var app = builder.Build();

// Apply migrations on startup
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    dbContext.Database.Migrate();
}

app.MapControllers();

// Map health check endpoints
app.MapHealthChecks("/health");
app.MapHealthChecks("/health/database", new HealthCheckOptions { Predicate = check => check.Name == "database" });
app.MapHealthChecks("/health/api", new HealthCheckOptions { Predicate = check => check.Tags.Contains("api") });

app.Run();
