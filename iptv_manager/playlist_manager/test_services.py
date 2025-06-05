import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from .models import PlaylistSource, PlaylistSourceChannel, PlaylistSourceInvocation
from .services import PlaylistSynchronizer

class PlaylistSynchronizerTestCase(TestCase):
    def setUp(self):
        # Create a test playlist source
        self.playlist_source = PlaylistSource.objects.create(
            name="Test Playlist",
            url="http://example.com/playlist.m3u",
            is_enabled=True
        )
        
        # Create some test channels
        self.channel1 = PlaylistSourceChannel.objects.create(
            source=self.playlist_source,
            title="Channel 1",
            tvg_id="channel1",
            media_url="http://example.com/channel1.m3u8",
            logo_url="http://example.com/channel1.png",
            group="Group 1",
            is_active=True
        )
        
        self.channel2 = PlaylistSourceChannel.objects.create(
            source=self.playlist_source,
            title="Channel 2",
            tvg_id="channel2",
            media_url="http://example.com/channel2.m3u8",
            logo_url="http://example.com/channel2.png",
            group="Group 2",
            is_active=True
        )
        
        # Initialize the synchronizer
        self.synchronizer = PlaylistSynchronizer()
        
        # Mock the config store
        self.synchronizer.config_store = MagicMock()
        self.synchronizer.config_store.get.return_value = {"allow_channel_auto_deletion": True}
        self.synchronizer.allow_channel_auto_deletion = True
    
    @patch('requests.get')
    def test_sync_success(self, mock_get):
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.text = """#EXTM3U
#EXTINF:-1 tvg-id="channel1" tvg-logo="http://example.com/channel1_new.png" group-title="Group 1",Channel 1
http://example.com/channel1_new.m3u8
#EXTINF:-1 tvg-id="channel3" tvg-logo="http://example.com/channel3.png" group-title="Group 3",Channel 3
http://example.com/channel3.m3u8
"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock the M3uParser
        with patch('playlist_manager.services.M3uParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Mock the parsed streams
            mock_parser.get_list.return_value = [
                {
                    'name': 'Channel 1',
                    'tvg': {'id': 'channel1', 'logo': 'http://example.com/channel1_new.png'},
                    'url': 'http://example.com/channel1_new.m3u8',
                    'group': 'Group 1'
                },
                {
                    'name': 'Channel 3',
                    'tvg': {'id': 'channel3', 'logo': 'http://example.com/channel3.png'},
                    'url': 'http://example.com/channel3.m3u8',
                    'group': 'Group 3'
                }
            ]
            
            # Call the sync method
            result = self.synchronizer.sync(self.playlist_source.id)
            
            # Check that the sync was successful
            self.assertTrue(result)
            
            # Check that an invocation was created
            invocation = PlaylistSourceInvocation.objects.first()
            self.assertIsNotNone(invocation)
            self.assertTrue(invocation.completed)

            # Check that Channel 1 was updated
            channel1 = PlaylistSourceChannel.objects.get(title="Channel 1", group="Group 1")
            self.assertEqual(channel1.media_url, "http://example.com/channel1_new.m3u8")
            self.assertEqual(channel1.logo_url, "http://example.com/channel1_new.png")
            
            # Check that Channel 2 was deleted (since allow_channel_auto_deletion is True)
            with self.assertRaises(PlaylistSourceChannel.DoesNotExist):
                PlaylistSourceChannel.objects.get(title="Channel 2")
            
            # Check that Channel 3 was created
            channel3 = PlaylistSourceChannel.objects.get(title="Channel 3")
            self.assertEqual(channel3.tvg_id, "channel3")
            self.assertEqual(channel3.media_url, "http://example.com/channel3.m3u8")
            self.assertEqual(channel3.logo_url, "http://example.com/channel3.png")
            self.assertEqual(channel3.group, "Group 3")
            self.assertTrue(channel3.is_active)
    
    @patch('requests.get')
    def test_sync_with_auto_deletion_disabled(self, mock_get):
        # Set allow_channel_auto_deletion to False
        self.synchronizer.allow_channel_auto_deletion = False
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.text = """#EXTM3U
#EXTINF:-1 tvg-id="channel1" tvg-logo="http://example.com/channel1.png" group-title="Group 1",Channel 1
http://example.com/channel1.m3u8
"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock the M3uParser
        with patch('playlist_manager.services.M3uParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Mock the parsed streams (only Channel 1)
            mock_parser.get_list.return_value = [
                {
                    'name': 'Channel 1',
                    'tvg': {'id': 'channel1', 'logo': 'http://example.com/channel1.png'},
                    'url': 'http://example.com/channel1.m3u8',
                    'group': 'Group 1'
                }
            ]
            
            # Call the sync method
            result = self.synchronizer.sync(self.playlist_source.id)
            
            # Check that the sync was successful
            self.assertTrue(result)
            
            # Check that Channel 2 was not deleted but set to inactive
            channel2 = PlaylistSourceChannel.objects.get(title="Channel 2")
            self.assertFalse(channel2.is_active)
    
    @patch('requests.get')
    def test_sync_error_handling(self, mock_get):
        # Mock the HTTP response to raise an exception
        mock_get.side_effect = Exception("Test error")
        
        # Call the sync method
        result = self.synchronizer.sync(self.playlist_source.id)
        
        # Check that the sync failed
        self.assertFalse(result)
        
        # Check that an invocation was created with an error
        invocation = PlaylistSourceInvocation.objects.first()
        self.assertIsNotNone(invocation)
        self.assertIn("Test error", invocation.error)
        self.assertTrue(invocation.completed)