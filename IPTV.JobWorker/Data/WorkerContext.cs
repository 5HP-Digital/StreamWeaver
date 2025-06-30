using IPTV.JobWorker.Data.Comparers;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace IPTV.JobWorker.Data;

public class WorkerContext(IConfiguration config, ILoggerFactory loggerFactory, TimeProvider timeProvider) : DbContext
{
    // Jobs
    public DbSet<Job> Jobs { get; set; }
    
    // Provider Streams
    public DbSet<ProviderStream> Streams { get; set; }

    // Guides
    public DbSet<Category> Categories { get; set; }
    public DbSet<Channel> Channels { get; set; }
    public DbSet<Country> Countries { get; set; }
    public DbSet<Guide> Guides { get; set; }

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

        // ProviderSyncJob
        modelBuilder.Entity<ProviderSyncJob>(builder =>
        {
            // Properties
            builder.Property(e => e.AllowStreamAutoDeletion)
                .IsRequired()
                .HasDefaultValue(true);

            // Relationships
            builder.HasOne(e => e.Provider)
                .WithMany(e => e.Jobs)
                .IsRequired()
                .HasForeignKey("provider_id")
                .OnDelete(DeleteBehavior.Cascade);
        });
        
        // EpgDataSyncJob
        modelBuilder.Entity<EpgDataSyncJob>(_ =>
        {
            // Properties
        });
        
        // PlaylistEpgGenJob
        modelBuilder.Entity<PlaylistEpgGenJob>(builder =>
        {
            // Relationships
            builder.HasOne(e => e.Playlist)
                .WithMany()
                .IsRequired()
                .HasForeignKey("playlist_id")
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Job
        modelBuilder.Entity<Job>(builder =>
        {
            // Table
            builder.ToTable("job_manager_job");
            builder.HasKey(e => e.Id);
            builder.HasDiscriminator(j => j.Type)
                .HasValue<ProviderSyncJob>(JobType.ProviderSync)
                .HasValue<EpgDataSyncJob>(JobType.EpgDataSync)
                .HasValue<PlaylistEpgGenJob>(JobType.PlaylistEpgGen);

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
                .HasSentinel(JobState.Queued)
                .HasConversion<EnumToStringConverter<JobState>>();

            builder.Property(e => e.StatusDescription)
                .HasColumnType("text");

            builder.Property(e => e.AttemptCount)
                .IsRequired()
                .HasDefaultValue(0);

            builder.Property(e => e.LastAttemptStartedAt);

            builder.Property(e => e.MaxAttempts);

            builder.Property(e => e.Type)
                .HasColumnType("varchar(20)")
                .IsRequired()
                .HasConversion<EnumToStringConverter<JobType>>();

            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            // Indexes
            builder.HasIndex(nameof(ProviderSyncJob.JobId))
                .IsUnique();

            builder.HasIndex(nameof(ProviderSyncJob.State), nameof(Job.CreatedAt));
        });

        // Provider
        modelBuilder.Entity<Provider>(builder =>
        {
            // Table
            builder.ToTable("provider_manager_provider");
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
            builder.HasMany(e => e.Streams)
                .WithOne()
                .HasForeignKey("provider_id")
                .OnDelete(DeleteBehavior.Cascade);
            builder.HasMany(e => e.Jobs)
                .WithOne(e => e.Provider)
                .HasForeignKey("provider_id")
                .OnDelete(DeleteBehavior.Cascade);
        });

        // ProviderStream
        modelBuilder.Entity<ProviderStream>(builder =>
        {
            // Table
            builder.ToTable("provider_manager_providerstream");
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
            
            // Relationships
            builder.HasOne(e => e.Provider)
                .WithMany(e => e.Streams)
                .HasForeignKey("provider_id")
                .OnDelete(DeleteBehavior.Cascade);
        });
        
        // Playlist
        modelBuilder.Entity<Playlist>(builder =>
        {
            // Table
            builder.ToTable("playlist_manager_playlist");
            builder.HasKey(e => e.Id);
            
            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();
            builder.Property(e => e.Name)
                .HasMaxLength(255)
                .IsRequired();
            builder.Property(e => e.StartingChannelNumber)
                .IsRequired();
            builder.Property(e => e.DefaultLang)
                .HasMaxLength(20)
                .IsRequired();
            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
            
            // Relationships
            builder.HasMany(e => e.Channels)
                .WithOne(e => e.Playlist)
                .HasForeignKey("playlist_id")
                .OnDelete(DeleteBehavior.Cascade);
        });
        
        // PlaylistChannel
        modelBuilder.Entity<PlaylistChannel>(builder =>
        {
            // Table
            builder.ToTable("playlist_manager_playlistchannel");
            builder.HasKey(e => e.Id);
            
            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.Title)
                .HasMaxLength(255);

            builder.Property(e => e.LogoUrl)
                .HasColumnType("text");

            builder.Property(e => e.Category)
                .HasMaxLength(255);

            builder.Property(e => e.Order)
                .IsRequired();

            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();

            // Relationships
            builder.HasOne(e => e.Guide)
                .WithMany(e => e.PlaylistChannels)
                .HasForeignKey("guide_id")
                .OnDelete(DeleteBehavior.SetNull);

            builder.HasOne(e => e.Stream)
                .WithMany()
                .HasForeignKey("stream_id")
                .OnDelete(DeleteBehavior.Cascade)
                .IsRequired();

            builder.HasOne(e => e.Playlist)
                .WithMany(e => e.Channels)
                .HasForeignKey("playlist_id")
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Category
        modelBuilder.Entity<Category>(builder =>
        {
            // Table
            builder.ToTable("guide_manager_category");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.Code)
                .HasMaxLength(20)
                .IsRequired();

            builder.Property(e => e.Name)
                .HasMaxLength(255)
                .IsRequired();

            // Indexes
            builder.HasIndex(e => e.Code)
                .IsUnique();
        });

        // Country
        modelBuilder.Entity<Country>(builder =>
        {
            // Table
            builder.ToTable("guide_manager_country");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.Code)
                .HasMaxLength(20)
                .IsRequired();

            builder.Property(e => e.Name)
                .HasMaxLength(255)
                .IsRequired();

            builder.Property(e => e.Flag)
                .HasMaxLength(20);

            // Indexes
            builder.HasIndex(e => e.Code)
                .IsUnique();
        });

        // Channel
        modelBuilder.Entity<Channel>(builder =>
        {
            // Table
            builder.ToTable("guide_manager_channel");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.XmltvId)
                .HasMaxLength(20)
                .IsRequired();

            builder.Property(e => e.Name)
                .HasMaxLength(255)
                .IsRequired();

            builder.Property(e => e.Network)
                .HasMaxLength(255);
            
            builder.Property(e => e.Country)
                .HasMaxLength(20)
                .IsRequired();

            builder.Property(e => e.City)
                .HasMaxLength(255);

            builder.Property(e => e.Categories)
                .HasMaxLength(255)
                .HasConversion<string>(arr => string.Join(';', arr),
                    str => str.Split(';', StringSplitOptions.RemoveEmptyEntries))
                .Metadata.SetValueComparer(new StringArrayComparer());

            builder.Property(e => e.IsNsfw)
                .IsRequired()
                .HasDefaultValue(false);

            builder.Property(e => e.LaunchedAt);

            builder.Property(e => e.ClosedAt);

            builder.Property(e => e.WebsiteUrl)
                .HasColumnType("text");

            builder.Property(e => e.LogoUrl)
                .HasColumnType("text");

            // Relationships

            // Indexes
        });

        // Guide
        modelBuilder.Entity<Guide>(builder =>
        {
            // Table
            builder.ToTable("guide_manager_guide");
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();

            builder.Property(e => e.Site)
                .HasMaxLength(255)
                .IsRequired();

            builder.Property(e => e.SiteId)
                .HasMaxLength(255)
                .IsRequired();

            builder.Property(e => e.SiteName)
                .HasMaxLength(255)
                .IsRequired();

            builder.Property(e => e.Lang)
                .HasMaxLength(20)
                .IsRequired();

            builder.Property(e => e.XmltvId)
                .HasMaxLength(20);

            // Relationships
            builder.HasMany(e => e.PlaylistChannels)
                .WithOne(e => e.Guide)
                .HasForeignKey("guide_id")
                .OnDelete(DeleteBehavior.SetNull);

            // Indexes
        });
    }

    public override int SaveChanges(bool acceptAllChangesOnSuccess)
    {
        UpdateTimestampProperties();

        return base.SaveChanges(acceptAllChangesOnSuccess);
    }

    public override Task<int> SaveChangesAsync(bool acceptAllChangesOnSuccess,
        CancellationToken cancellationToken = default)
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