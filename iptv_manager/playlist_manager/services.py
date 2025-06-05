import logging
import requests
from django.db import transaction
from django.core.exceptions import ValidationError
from m3u_parser import M3uParser
from iptv_manager.config_store import ConfigStore
from .models import PlaylistSource, PlaylistSourceChannel, PlaylistSourceInvocation

logger = logging.getLogger(__name__)

class PlaylistSynchronizer:
    """
    Service for synchronizing playlist channels from an m3u file.
    """

    def __init__(self):
        """Initialize the PlaylistSynchronizer."""
        self.config_store = ConfigStore()
        self.settings = self.config_store.get("iptv:settings", {})
        self.allow_channel_auto_deletion = self.settings.get("allow_channel_auto_deletion", True)

    def sync(self, playlist_source_id) -> bool:
        """
        Synchronize playlist channels from an m3u file.

        Args:
            playlist_source_id: The ID of the PlaylistSource to synchronize.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Step 1: Validate the ID argument and retrieve the PlaylistSource model
        try:
            playlist_source = PlaylistSource.objects.get(id=playlist_source_id)
        except (PlaylistSource.DoesNotExist, ValidationError):
            logger.error(f"Invalid playlist source ID: {playlist_source_id}")
            return False

        if not playlist_source.is_enabled:
            logger.error(f"Playlist source {playlist_source.name} is disabled")
            return False

        # Step 2: Create a PlaylistSourceInvocation record
        invocation = PlaylistSourceInvocation.objects.create(source=playlist_source)

        try:
            # Step 3: Use HTTP client to retrieve the m3u file
            response = requests.get(playlist_source.url, stream=True)
            response.raise_for_status()

            # Step 4: Parse the m3u file content
            parser = M3uParser(timeout=60)
            parser.parse_m3u(response.text)
            streams = parser.get_list()

            # Step 5: Synchronize the parsed streams with the database
            self._synchronize_streams(playlist_source, streams)

            return True
        except Exception as e:
            # Step 6: Log any errors
            error_message = f"Error synchronizing playlist source {playlist_source.name}: {str(e)}"
            logger.error(error_message)
            invocation.error = error_message
            return False
        finally:
            # Step 7: Mark the invocation as completed
            invocation.completed = True
            invocation.save()

    @transaction.atomic
    def _synchronize_streams(self, playlist_source, streams):
        """
        Synchronize the parsed streams with the database.

        Args:
            playlist_source: The PlaylistSource model.
            streams: The parsed streams from the m3u file.
        """
        # Get existing channels for the playlist source
        existing_channels = {
            (channel.title, channel.group): channel
            for channel in PlaylistSourceChannel.objects.filter(source=playlist_source)
        }

        # Track which channels were processed
        processed_channels = set()

        # Process each stream from the m3u file
        for stream in streams:
            title = stream.get('name', '')
            group = stream.get('group', '')
            key = (title, group)

            # Skip streams without a title or media URL
            if not title or not stream.get('url'):
                continue

            # Check if the channel already exists
            if key in existing_channels:
                # Update existing channel
                channel = existing_channels[key]
                modified = False

                # Check if any fields need to be updated
                if channel.tvg_id != stream.get('tvg', {}).get('id', '') and stream.get('tvg', {}).get('id', ''):
                    channel.tvg_id = stream.get('tvg', {}).get('id', '')
                    modified = True

                if channel.media_url != stream.get('url', ''):
                    channel.media_url = stream.get('url', '')
                    modified = True

                if channel.logo_url != stream.get('tvg', {}).get('logo', '') and stream.get('tvg', {}).get('logo', ''):
                    channel.logo_url = stream.get('tvg', {}).get('logo', '')
                    modified = True

                if not channel.is_active:
                    channel.is_active = True
                    modified = True

                # Save only if modified
                if modified:
                    channel.save()
            else:
                # Create new channel
                PlaylistSourceChannel.objects.create(
                    source=playlist_source,
                    title=title,
                    tvg_id=stream.get('tvg', {}).get('id', ''),
                    media_url=stream.get('url', ''),
                    logo_url=stream.get('tvg', {}).get('logo', ''),
                    group=group,
                    is_active=True
                )

            # Mark as processed
            processed_channels.add(key)

        # Handle channels that weren't in the m3u file
        for key, channel in existing_channels.items():
            if key not in processed_channels:
                if self.allow_channel_auto_deletion:
                    # Delete the channel
                    channel.delete()
                else:
                    # Set is_active to False
                    if channel.is_active:
                        channel.is_active = False
                        channel.save()
