# Generated by Django 4.2.7 on 2025-06-12 05:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('playlist_manager', '0002_playlistchannel_tvg_id'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='playlist',
            name='unique_playlist_order',
        ),
        migrations.RemoveIndex(
            model_name='playlist',
            name='playlist_order_idx',
        ),
        migrations.RemoveField(
            model_name='playlist',
            name='order',
        ),
    ]
