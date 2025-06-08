using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace IPTV.JobWorker.Data;

public class WorkerContext(IConfiguration config) : DbContext
{
    public DbSet<Job> Jobs { get; set; }
    
    public DbSet<PlaylistSource> PlaylistSources { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        // Construct the path to the SQLite database file using the CONFIG_DIR environment variable
        var dbPath = Path.Combine(config["CONFIG_DIR"]!, "db.sqlite3");
        optionsBuilder.UseSqlite($"Filename={dbPath}")
            .UseSnakeCaseNamingConvention()
            .UseLazyLoadingProxies();
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        // Job
        modelBuilder.Entity<Job>(builder =>
        {
            // Table
            builder.HasKey(e => e.Id);

            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();
            
            builder.Property(e => e.JobId)
                .IsRequired()
                .HasConversion<GuidToStringConverter>();

            builder.Property(e => e.State)
                .IsRequired()
                .HasConversion<EnumToStringConverter<JobState>>();
            
            builder.Property(e => e.AttemptCount)
                .IsRequired()
                .HasDefaultValue(0);

            builder.Property(e => e.Error);
            
            builder.Property(e => e.Context)
                .IsRequired();
            
            builder.Property(e => e.CreatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
            
            builder.Property(e => e.UpdatedAt)
                .ValueGeneratedOnAdd()
                .IsRequired();
            
            // Indexes
            builder.HasIndex(nameof(Job.JobId))
                .IsUnique();
        });

        // PlaylistSource
        modelBuilder.Entity<PlaylistSource>(builder =>
        {
            // Table
            builder.HasKey(e => e.Id);
            
            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();
            builder.Property(e => e.Name)
                .IsRequired();
            builder.Property(e => e.Url)
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
        });

        // PlaylistSourceChannel
        modelBuilder.Entity<PlaylistSourceChannel>(builder =>
        {
            // Table
            builder.HasKey(e => e.Id);
            
            // Properties
            builder.Property(e => e.Id)
                .ValueGeneratedOnAdd();
            
            builder.Property(e => e.Title)
                .IsRequired();
            
            builder.Property(e => e.TvgId)
                .IsRequired();
            
            builder.Property(e => e.MediaUrl)
                .IsRequired();
            
            builder.Property(e => e.LogoUrl);
            
            builder.Property(e => e.Group);
            
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
}