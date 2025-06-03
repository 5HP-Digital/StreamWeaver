namespace IPTV.PlaylistManager.Data;

using Microsoft.EntityFrameworkCore;

using TimeProvider = Digital5HP.TimeProvider;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<PlaylistSource> PlaylistSources { get; set; }
    public DbSet<PlaylistSourceChannel> PlaylistSourceChannels { get; set; }
    public DbSet<PlaylistSourceInvocation> PlaylistSourceInvocations { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        base.OnConfiguring(optionsBuilder);
        
        optionsBuilder.EnableDetailedErrors()
            .EnableSensitiveDataLogging()
            .UseSnakeCaseNamingConvention();
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        // PlaylistSource
        modelBuilder.Entity<PlaylistSource>(entity =>
        {
            entity.Property(e => e.Name).HasColumnType("character varying(255)").IsRequired();
            entity.Property(e => e.Url).HasColumnType("text").IsRequired();
            entity.Property(e => e.CreatedAt)
                .HasColumnType("timestamp with time zone")
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .ValueGeneratedOnAdd();
            entity.Property(e => e.UpdatedAt)
                .HasColumnType("timestamp with time zone")
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .ValueGeneratedOnAddOrUpdate();

            entity.HasMany(e => e.Invocations)
                .WithOne()
                .HasForeignKey("playlist_source_id")
                .OnDelete(DeleteBehavior.Cascade);
            
            entity.HasMany(e => e.Channels)
                .WithOne()
                .HasForeignKey("playlist_source_id")
                .OnDelete(DeleteBehavior.Cascade);
        });
        
        // PlaylistSourceInvocation
        modelBuilder.Entity<PlaylistSourceInvocation>(entity =>
        {
            entity.Property(e => e.Error).HasColumnType("text").IsRequired(false);
            entity.Property(e => e.CreatedAt)
                .HasColumnType("timestamp with time zone")
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .ValueGeneratedOnAdd();
            entity.Property(e => e.UpdatedAt)
                .HasColumnType("timestamp with time zone")
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .ValueGeneratedOnAddOrUpdate();
        });
        
        // PlaylistSourceChannel
        modelBuilder.Entity<PlaylistSourceChannel>(entity =>
        {
            entity.Property(e => e.MediaUrl)
                .HasColumnType("text")
                .IsRequired();
            entity.Property(e => e.TvgId)
                .HasColumnType("character varying(255)")
                .IsRequired();
            entity.Property(e => e.LogoUrl)
                .HasColumnType("text")
                .IsRequired(false);
            entity.Property(e => e.Group)
                .HasColumnType("character varying(255)")
                .IsRequired(false);
            entity.Property(e => e.Title)
                .HasColumnType("character varying(255)")
                .IsRequired(false);
            entity.Property(e => e.CreatedAt)
                .HasColumnType("timestamp with time zone")
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .ValueGeneratedOnAdd();
            entity.Property(e => e.UpdatedAt)
                .HasColumnType("timestamp with time zone")
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .ValueGeneratedOnAddOrUpdate();
        });
        
    }

    public override int SaveChanges(bool acceptAllChangesOnSuccess)
    {
        UpdateAuditProperties();
        
        return base.SaveChanges(acceptAllChangesOnSuccess);
    }

    public override Task<int> SaveChangesAsync(bool acceptAllChangesOnSuccess, CancellationToken cancellationToken = new CancellationToken())
    {
        UpdateAuditProperties();
        
        return base.SaveChangesAsync(acceptAllChangesOnSuccess, cancellationToken);
    }

    private void UpdateAuditProperties()
    {
        var entries = ChangeTracker
            .Entries()
            .Where(e => e is { Entity: IEntity, State: EntityState.Added or EntityState.Modified });

        foreach (var entityEntry in entries)
        {
            ((IEntity)entityEntry.Entity).UpdatedAt = TimeProvider.Current.Now;

            if (entityEntry.State == EntityState.Added)
            {
                ((IEntity)entityEntry.Entity).CreatedAt = TimeProvider.Current.Now;
            }
        }
    }
}