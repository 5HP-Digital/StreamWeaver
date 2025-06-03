using IPTV.PlaylistManager.Data;
using IPTV.PlaylistManager.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace IPTV.PlaylistManager.Controllers;

[ApiController]
[Route("sources/{id}/[controller]")]
public class ChannelsControllers(AppDbContext context) : ControllerBase
{
    [HttpGet("channels")]
    public async Task<ActionResult<PaginatedResponse<PlaylistSourceChannelModel>>> GetSourceChannels(
        long id,
        [FromQuery] int page = 1,
        [FromQuery] int size = 10,
        CancellationToken cancellationToken = default)
    {
        // Validate pagination parameters
        if (page < 1)
        {
            return BadRequest("Page number must be greater than or equal to 1");
        }

        if (size < 1 || size > 100)
        {
            return BadRequest("Page size must be between 1 and 100");
        }

        // Check if source exists
        var source = await context.PlaylistSources
            .FirstOrDefaultAsync(s => s.Id == id, cancellationToken);

        if (source == null)
        {
            return NotFound($"PlaylistSource with ID {id} was not found");
        }

        // Get total count of channels for this source
        var query = context.PlaylistSourceChannels
            .Where(c => source.Channels.Contains(c));
        
        var totalItems = await query.CountAsync(cancellationToken);

        // Calculate pagination values
        var totalPages = (int)Math.Ceiling(totalItems / (double)size);
        var skip = (page - 1) * size;

        // Get the channels for the current page
        var channels = await query.OrderBy(c => c.TvgId)
            .Skip(skip)
            .Take(size)
            .ToListAsync(cancellationToken);

        // Create response with pagination links
        var baseUrl = $"{Request.Scheme}://{Request.Host}{Request.PathBase}{Request.Path}";

        var response = new PaginatedResponse<PlaylistSourceChannelModel>
        {
            Page = page,
            Total = totalItems,
            Items = channels.Select(c => new PlaylistSourceChannelModel
            {
                Id = c.Id,
                Title = c.Title,
                TvgId = c.TvgId,
                MediaUrl = c.MediaUrl,
                LogoUrl = c.LogoUrl,
                Group = c.Group,
                CreatedAt = c.CreatedAt,
                UpdatedAt = c.UpdatedAt
            }),
            Links = new PaginatedResponse<PlaylistSourceChannelModel>.PageLinks()
        };

        // Add pagination links
        if (page > 1)
        {
            response.Links.First = $"{baseUrl}?page=1&size={size}";
            response.Links.Previous = $"{baseUrl}?page={page - 1}&size={size}";
        }

        if (page < totalPages)
        {
            response.Links.Next = $"{baseUrl}?page={page + 1}&size={size}";
            response.Links.Last = $"{baseUrl}?page={totalPages}&size={size}";
        }

        return response;
    }
}