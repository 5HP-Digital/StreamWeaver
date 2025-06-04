using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace IPTV.PlaylistManager.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddIsActiveAndIsEnabledColumns : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "is_enabled",
                table: "playlist_sources",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "is_active",
                table: "playlist_source_channels",
                type: "boolean",
                nullable: false,
                defaultValue: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "is_enabled",
                table: "playlist_sources");

            migrationBuilder.DropColumn(
                name: "is_active",
                table: "playlist_source_channels");
        }
    }
}
