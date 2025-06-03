namespace IPTV.PlaylistManager.Controllers;

using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

using IPTV.PlaylistManager.Data;
using IPTV.PlaylistManager.Models;
using IPTV.PlaylistManager.Services;

[ApiController]
[Route("[controller]")]
public class SourcesController(AppDbContext context, PlaylistReader playlistReader) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<IEnumerable<PlaylistSourceModel>>> GetSources()
    {
        return (await context.PlaylistSources.ToListAsync())
            .Select(MapToModel)
            .ToList();
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<PlaylistSourceModel>> GetSource(int id)
    {
        var source = await context.PlaylistSources
            .Include(s => s.Invocations)
            .FirstOrDefaultAsync(s => s.Id == id);

        if (source == null)
        {
            return NotFound();
        }
        
        return MapToModel(source);
    }

    [HttpPost]
    public async Task<ActionResult<PlaylistSourceModel>> CreateSource(PlaylistSourceCreateModel model)
    {
        var entity = new PlaylistSource
        {
            Name = model.Name,
            Url = model.Url
        };
        
        context.PlaylistSources.Add(entity);
        await context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetSource), new { id = entity.Id }, entity);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateSource(long id, PlaylistSourceUpdateModel model)
    {
        var existingSource = await context.PlaylistSources.FindAsync(id);
        if (existingSource == null)
        {
            return NotFound();
        }

        existingSource.Name = model.Name;
        existingSource.Url = model.Url;

        try
        {
            await context.SaveChangesAsync();
        }
        catch (DbUpdateConcurrencyException)
        {
            if (!await SourceExists(id))
            {
                return NotFound();
            }
            throw;
        }

        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteSource(long id)
    {
        var source = await context.PlaylistSources.FindAsync(id);
        if (source == null)
        {
            return NotFound();
        }

        context.PlaylistSources.Remove(source);
        await context.SaveChangesAsync();

        return NoContent();
    }

    // [HttpGet("{id}/channels")]
    // public async Task<ActionResult<IEnumerable<PlaylistChannelModel>>> GetSourceChannels(long id,
    //     CancellationToken cancellationToken)
    // {
    //     var source = await context.PlaylistSources.FindAsync([id], cancellationToken: cancellationToken);
    //     if (source == null)
    //     {
    //         return NotFound();
    //     }
    //
    //     try
    //     {
    //         var document = await playlistReader.ReadAsync(source.Url, cancellationToken);
    //
    //         return document.Channels.Select(entry => new PlaylistChannelModel
    //         {
    //             MediaUrl = entry.MediaUrl,
    //             TvgId = entry.TvgId,
    //             TvgName = entry.TvgName,
    //             TvgChannelNumber = entry.TvgChannelNumber,
    //             ChannelId = entry.ChannelId,
    //             ChannelNumber = entry.ChannelNumber,
    //             Duration = entry.Duration,
    //             Title = entry.Title,
    //             LogoUrl = entry.LogoUrl,
    //             GroupTitle = entry.GroupTitle
    //         }).ToList();
    //     }
    //     catch (PlaylistException ex)
    //     {
    //         return Problem($"Failed to process playlist: {ex.Message}", statusCode: 500);
    //     }
    // }
    
    private async Task<bool> SourceExists(long id)
    {
        return await context.PlaylistSources.AnyAsync(e => e.Id == id);
    }

    private static PlaylistSourceModel MapToModel(PlaylistSource source)
    {
        return new PlaylistSourceModel
        {
            Id = source.Id,
            Name = source.Name,
            Url = source.Url,
            CreatedAt = source.CreatedAt,
            UpdatedAt = source.UpdatedAt
        };
    }
}