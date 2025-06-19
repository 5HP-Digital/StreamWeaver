using System.Text.Json;
using EFCore.BulkExtensions;
using IPTV.JobWorker.Data;
using Microsoft.EntityFrameworkCore;

namespace IPTV.JobWorker.Services;

public class EpgOrgDataSynchronizer(
    WorkerContext workerContext, 
    IHttpClientFactory httpClientFactory, 
    ILogger<EpgOrgDataSynchronizer> logger)
{
    private const string CountryApiUrl = "https://iptv-org.github.io/api/countries.json";
    private const string CategoryApiUrl = "https://iptv-org.github.io/api/categories.json";
    private const string GuideApiUrl = "https://iptv-org.github.io/api/guides.json";
    private const string ChannelApiUrl = "https://iptv-org.github.io/api/channels.json";
    
    public async Task<(bool, string)> Run(CancellationToken cancellationToken)
    {
        using var client = httpClientFactory.CreateClient();

        int countriesCount, categoriesCount, channelsCount, guidesCount;
        
        // Sync countries
        await using (var countryStream = await client.GetStreamAsync(CountryApiUrl, cancellationToken))
        {
            var jsonCountries = await JsonSerializer.DeserializeAsync<JsonCountry[]>(countryStream, cancellationToken: cancellationToken);

            if (jsonCountries is null)
            {
                logger.LogError("Failed to deserialize countries");
                return (false, "Failed to deserialize countries");
            }
            
            var countries = await workerContext.Countries.AsNoTracking().ToListAsync(cancellationToken);

            // Create lookup of existing countries
            var existingCountries = countries.ToDictionary(c => c.Code);

            // Process JSON countries
            var countriesToAdd = new List<Country>();
            var countriesToUpdate = new List<Country>();
            foreach (var jsonCountry in jsonCountries)
            {
                if (existingCountries.TryGetValue(jsonCountry.code, out var country))
                {
                    // Update existing country
                    country.Name = jsonCountry.name;
                    country.Flag = jsonCountry.flag;
                    
                    countriesToUpdate.Add(country);
                }
                else
                {
                    // Add new country
                    countriesToAdd.Add(new Country
                    {
                        Code = jsonCountry.code,
                        Name = jsonCountry.name,
                        Flag = jsonCountry.flag
                    });
                }
            }

            // Remove countries that don't exist in JSON
            var validCodes = jsonCountries.Select(c => c.code).ToHashSet();
            var countriesToRemove = countries.Where(c => !validCodes.Contains(c.Code)).ToList();
            
            // Save changes
            await workerContext.BulkInsertAsync(countriesToAdd, cancellationToken: cancellationToken);
            await workerContext.BulkUpdateAsync(countriesToUpdate, cancellationToken: cancellationToken);
            await workerContext.BulkDeleteAsync(countriesToRemove, cancellationToken: cancellationToken);

            logger.LogInformation("Countries synced ({Added} added;{Updated} updated;{Removed} removed)", 
                countriesToAdd.Count, countriesToUpdate.Count, countriesToRemove.Count);
            
            countriesCount = jsonCountries.Length;
        }
        
        // Sync categories
        await using (var categoryStream = await client.GetStreamAsync(CategoryApiUrl, cancellationToken))
        {
            var jsonCategories = await JsonSerializer.DeserializeAsync<JsonCategory[]>(categoryStream, cancellationToken: cancellationToken);

            if (jsonCategories is null)
            {
                logger.LogError("Failed to deserialize categories");
                return (false, "Failed to deserialize categories");
            }
            
            var categories = await workerContext.Categories.AsNoTracking().ToListAsync(cancellationToken);

            // Create lookup of existing categories
            var existingCategories = categories.ToDictionary(c => c.Code);

            // Process JSON categories
            var categoriesToAdd = new List<Category>();
            var categoriesToUpdate = new List<Category>();
            foreach (var jsonCategory in jsonCategories)
            {
                if (existingCategories.TryGetValue(jsonCategory.id, out var category))
                {
                    // Update existing category
                    category.Name = jsonCategory.name;

                    categoriesToUpdate.Add(category);
                }
                else
                {
                    // Add new category
                    categoriesToAdd.Add(new Category
                    {
                        Code = jsonCategory.id,
                        Name = jsonCategory.name
                    });
                }
            }

            // Remove categories that don't exist in JSON
            var validCodes = jsonCategories.Select(c => c.id).ToHashSet();
            var categoriesToRemove = categories.Where(c => !validCodes.Contains(c.Code)).ToList();
            
            // Save changes
            await workerContext.BulkInsertAsync(categoriesToAdd, cancellationToken: cancellationToken);
            await workerContext.BulkUpdateAsync(categoriesToUpdate, cancellationToken: cancellationToken);
            await workerContext.BulkDeleteAsync(categoriesToRemove, cancellationToken: cancellationToken);

            logger.LogInformation("Categories synced ({Added} added;{Updated} updated;{Removed} removed)", 
                categoriesToAdd.Count, categoriesToUpdate.Count, categoriesToRemove.Count);
            
            categoriesCount = jsonCategories.Length;
        }
        
        // Sync channels
        await using (var channelStream = await client.GetStreamAsync(ChannelApiUrl, cancellationToken))
        {
            var jsonChannels = await JsonSerializer.DeserializeAsync<JsonChannel[]>(channelStream, cancellationToken: cancellationToken);
            if (jsonChannels is null)
            {
                logger.LogError("Failed to deserialize channels");
                return (false, "Failed to deserialize channels");
            }
            
            var channels = await workerContext.Channels.AsNoTracking().ToListAsync(cancellationToken);

            // Create lookup of existing channels
            var existingChannels = channels.ToDictionary(c => c.XmltvId);

            // Process JSON channels
            var channelsToAdd = new List<Channel>();
            var channelsToUpdate = new List<Channel>();
            foreach (var jsonChannel in jsonChannels)
            {
                if (existingChannels.TryGetValue(jsonChannel.id, out var channel))
                {
                    // Update existing channel
                    channel.Name = jsonChannel.name;
                    channel.Network = jsonChannel.network;
                    channel.Country = jsonChannel.country;
                    channel.City = jsonChannel.city;
                    channel.Categories = jsonChannel.categories;
                    channel.IsNsfw = jsonChannel.is_nsfw;
                    channel.LaunchedAt = DateOnly.TryParse(jsonChannel.launched, out var launched) ? launched : default;
                    channel.ClosedAt = DateOnly.TryParse(jsonChannel.closed, out var closed) ? closed : default;
                    channel.LogoUrl = jsonChannel.logo;
                    channel.WebsiteUrl = jsonChannel.website;

                    channelsToUpdate.Add(channel);
                }
                else
                {
                    // Add new channel
                    channelsToAdd.Add(new Channel
                    {
                        XmltvId = jsonChannel.id,
                        Name = jsonChannel.name,
                        Network = jsonChannel.network,
                        Country = jsonChannel.country,
                        City = jsonChannel.city,
                        Categories = jsonChannel.categories,
                        IsNsfw = jsonChannel.is_nsfw,
                        LaunchedAt = DateOnly.TryParse(jsonChannel.launched, out var launched) ? launched : default,
                        ClosedAt = DateOnly.TryParse(jsonChannel.closed, out var closed) ? closed : default,
                        LogoUrl = jsonChannel.logo,
                        WebsiteUrl = jsonChannel.website
                    });
                }
            }

            // Remove channels that don't exist in JSON
            var validCodes = jsonChannels.Select(c => c.id).ToHashSet();
            var channelsToRemove = channels.Where(c => !validCodes.Contains(c.XmltvId)).ToList();
            
            // Save changes
            await workerContext.BulkInsertAsync(channelsToAdd, cancellationToken: cancellationToken);
            await workerContext.BulkUpdateAsync(channelsToUpdate, cancellationToken: cancellationToken);
            await workerContext.BulkDeleteAsync(channelsToRemove, cancellationToken: cancellationToken);
            
            logger.LogInformation("Channels synced ({Added} added;{Updated} updated;{Removed} removed)", 
                channelsToAdd.Count, channelsToUpdate.Count, channelsToRemove.Count);
            
            channelsCount = jsonChannels.Length;
        }
        
        // Sync guides
        await using (var guideStream = await client.GetStreamAsync(GuideApiUrl, cancellationToken))
        {
            var jsonGuides = await JsonSerializer.DeserializeAsync<JsonGuide[]>(guideStream, cancellationToken: cancellationToken);
            if (jsonGuides is null)
            {
                logger.LogError("Failed to deserialize guides");
                return (false, "Failed to deserialize guides");
            }
            
            var guides = await workerContext.Guides.AsNoTracking().ToListAsync(cancellationToken);

            // Create lookup of existing guides
            var existingGuides = guides.GroupBy(g => (g.Site, g.SiteId, g.Lang))
                .ToDictionary(g => g.Key, g => g.ToList());

            // Process JSON guides
            var guidesToAdd = new List<Guide>();
            var guidesToUpdate = new List<Guide>();
            foreach (var jsonGuide in jsonGuides)
            {
                if (existingGuides.TryGetValue((jsonGuide.site, jsonGuide.site_id, jsonGuide.lang), out var guidesForKey))
                {
                    foreach (var guide in guidesForKey)
                    {
                        // Update existing guide
                        guide.XmltvId = jsonGuide.channel;
                        guide.SiteName = jsonGuide.site_name;

                        guidesToUpdate.Add(guide);
                    }
                }
                else
                {
                    // Add new guide
                    guidesToAdd.Add(new Guide
                    {
                        XmltvId = jsonGuide.channel,
                        Site = jsonGuide.site,
                        SiteId = jsonGuide.site_id,
                        SiteName = jsonGuide.site_name,
                        Lang = jsonGuide.lang
                    });
                }
            }

            // Remove guides that don't exist in JSON
            var validKeys = jsonGuides.Select(g => (g.site, g.site_id, g.lang)).ToHashSet();
            var guidesToRemove = guides.Where(g => !validKeys.Contains((g.Site, g.SiteId, g.Lang))).ToList();
            
            // Save changes
            await workerContext.BulkInsertAsync(guidesToAdd, cancellationToken: cancellationToken);
            await workerContext.BulkUpdateAsync(guidesToUpdate, cancellationToken: cancellationToken);
            await workerContext.BulkDeleteAsync(guidesToRemove, cancellationToken: cancellationToken);

            logger.LogInformation("Guides synced ({Added} added;{Updated} updated;{Removed} removed)", 
                guidesToAdd.Count, guidesToUpdate.Count, guidesToRemove.Count);
            
            guidesCount = jsonGuides.Length;
        }
        
        return (true, $"Data synced (countries: {countriesCount}; categories: {categoriesCount}; channels: {channelsCount}; guides: {guidesCount})");
    }
    
    // Models
    // ReSharper disable ClassNeverInstantiated.Local
    private class JsonCountry
    {
        // ReSharper disable InconsistentNaming
        // ReSharper disable UnusedAutoPropertyAccessor.Local
        public required string name { get; set; }

        public required string code { get; set; }

        public string? flag { get; set; }
    }

    private class JsonCategory
    {
        public required string id { get; set; }

        public required string name { get; set; }
    }

    private class JsonChannel
    {
        public required string id { get; set; }

        public required string name { get; set; }

        public string? network { get; set; }

        public required string country { get; set; }
        
        public required string city { get; set; }

        public required string[] categories { get; init; } = [];
        
        public required bool is_nsfw { get; set; }
        
        public string? launched { get; set; }

        public string? closed { get; set; }
        
        public string? logo { get; set; }
        
        public string? website { get; set; }
    }

    private class JsonGuide
    {
        public string? channel { get; set; }
        
        public required string site { get; set; }
        
        public required string site_id { get; set; }
        
        public required string site_name { get; set; }
        
        public required string lang { get; set; }
        // ReSharper restore InconsistentNaming
        // ReSharper restore UnusedAutoPropertyAccessor.Local
    }
    // ReSharper restore ClassNeverInstantiated.Local
}