from django.db import models
from django.core.validators import URLValidator


class Country(models.Model):
    """
    Model representing a country.
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    flag = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Model representing a category.
    """
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Channel(models.Model):
    """
    Model representing a channel.
    """
    xmltv_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    network = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=20)
    city = models.CharField(max_length=255, null=True, blank=True)
    categories = models.CharField(max_length=255, null=True, blank=True)
    is_nsfw = models.BooleanField(default=False)
    launched_at = models.DateField(null=True, blank=True)
    closed_at = models.DateField(null=True, blank=True)
    website_url = models.TextField(validators=[URLValidator()], null=True, blank=True)
    logo_url = models.TextField(validators=[URLValidator()], null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['xmltv_id'], name='channel_xmltv_id_idx'),
        ]

    def __str__(self):
        return f'{self.name} ({self.xmltv_id})'


class Guide(models.Model):
    """
    Model representing a guide.
    """
    site = models.CharField(max_length=255)
    site_id = models.CharField(max_length=255)
    site_name = models.CharField(max_length=255)
    lang = models.CharField(max_length=20)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.SET_NULL,
        related_name='guides',
        to_field='xmltv_id',
        db_column='xmltv_id',
        db_index=True,
        null=True,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['site', 'site_id', 'site_name'], name='guide_site_site_id_name_idx'),
            models.Index(fields=['lang'], name='guide_lang_idx'),
        ]

    def __str__(self):
        return f"{self.site_name} - {self.site_id}"