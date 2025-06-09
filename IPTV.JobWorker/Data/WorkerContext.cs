using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace IPTV.JobWorker.Data;

public class WorkerContext(IConfiguration config, ILoggerFactory loggerFactory, TimeProvider timeProvider) : DbContext
{
    public DbSet<PlaylistSyncJob> Jobs { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        // Construct the path to the SQLite database file using the CONFIG_DIR environment variable
        var dbPath = Path.Combine(config["CONFIG_DIR"]!, "db.sqlite3");
        optionsBuilder.UseSqlite($"Data Source={dbPath}")
            .UseSnakeCaseNamingConvention()
            .UseLazyLoadingProxies()
            .EnableSensitiveDataLogging()
            .EnableDetailedErrors()
            .UseLoggerFactory(loggerFactory);
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Job
        modelBuilder.Entity<PlaylistSyncJob>(builder =>
        {
            // Table
            builder.ToTable("playlist_manager_playlistsyncjob");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.JobId)
                .HasColumnType("varchar(32)")
                .IsRequired()
                .HasConversion<GuidToStringConverter>();

            builder.Property(e => e.State)
                .HasColumnType("varchar(20)")
                .IsRequired()
                .HasDefaultValueSql("Queued")
                .HasConversion<EnumToStringConverter<JobState>>();

            builder.Property(e => e.StatusDescription)
                .HasColumnType("text");

            builder.Property(e => e.AttemptCount)
                .IsRequired()
                .HasDefaultValue(0);

            builder.Property(e => e.LastAttemptStartedAt);

            builder.Property(e => e.MaxAttempts);
            
            builder.Property(e => e.AllowChannelAutoDeletion)
                .IsRequired()
                .HasDefaultValue(true);

            builder.Property(e => e.Context)
                .HasColumnType("text")
                .IsRequired();

            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            // Relationships
            builder.HasOne(e => e.Source)
                .WithMany(e => e.Jobs)
                .IsRequired()
                .HasForeignKey("source_id")
                .OnDelete(DeleteBehavior.Cascade);
            
            // Indexes
            builder.HasIndex(nameof(PlaylistSyncJob.JobId))
                .IsUnique();
        });

        // PlaylistSource
        modelBuilder.Entity<PlaylistSource>(builder =>
        {
            // Table
            builder.ToTable("playlist_manager_playlistsource");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();
            builder.Property(e => e.Name)
                .HasMaxLength(255)
                .IsRequired();
            builder.Property(e => e.Url)
                .HasColumnType("text")
                .IsRequired();

            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            // Relationships
            builder.HasMany(e => e.Channels)
                .WithOne()
                .HasForeignKey("source_id")
                .OnDelete(DeleteBehavior.Cascade);
            builder.HasMany(e => e.Jobs)
                .WithOne(e => e.Source)
                .HasForeignKey("source_id")
                .OnDelete(DeleteBehavior.Cascade);
        });

        // PlaylistSourceChannel
        modelBuilder.Entity<PlaylistSourceChannel>(builder =>
        {
            // Table
            builder.ToTable("playlist_manager_playlistsourcechannel");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.Title)
                .HasMaxLength(255)
                .IsRequired();

            builder.Property(e => e.TvgId)
                .HasMaxLength(255);

            builder.Property(e => e.MediaUrl)
                .HasColumnType("text")
                .IsRequired();

            builder.Property(e => e.LogoUrl)
                .HasColumnType("text");

            builder.Property(e => e.Group)
                .HasMaxLength(255);

            builder.Property(e => e.IsActive)
                .IsRequired();

            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
        });
    }

    public override int SaveChanges(bool acceptAllChangesOnSuccess)
    {
        UpdateTimestampProperties();

        return base.SaveChanges(acceptAllChangesOnSuccess);
    }

    public override Task<int> SaveChangesAsync(bool acceptAllChangesOnSuccess,
        CancellationToken cancellationToken = new CancellationToken())
    {
        UpdateTimestampProperties();

        return base.SaveChangesAsync(acceptAllChangesOnSuccess, cancellationToken);
    }

    private void UpdateTimestampProperties()
    {
        foreach (var entry in ChangeTracker.Entries()
                     .Where(e => e is { Entity: ITimestampable, State: EntityState.Added or EntityState.Modified }))
        {
            var entity = (ITimestampable)entry.Entity;

            if (entry.State == EntityState.Added)
            {
                entity.CreatedAt = timeProvider.GetUtcNow().DateTime;
            }

            entity.UpdatedAt = timeProvider.GetUtcNow().DateTime;
        }
    }
}