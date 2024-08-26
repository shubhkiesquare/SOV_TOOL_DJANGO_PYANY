# search_app/models.py
from django.db import models
from django.utils import timezone

from django.db import models
from django.utils import timezone

class SearchQuery(models.Model):
    SEARCH_ENGINES = [
        ('google', 'Google Search'),
        ('bing', 'Bing'),
        ('yahoo', 'Yahoo'),
    ]

    COUNTRY_CHOICES = [
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('IN', 'India'),
    ]

    DEVICE_CHOICES = [
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ]

    search_engine = models.CharField(max_length=10, choices=SEARCH_ENGINES)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    city = models.CharField(max_length=255)  # Changed to CharField without choices
    pagination = models.CharField(max_length=3, blank=True)
    device = models.CharField(max_length=10, choices=DEVICE_CHOICES)
    keywords = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.search_engine} - {self.keywords[:50]} - {self.created_at}"

class SearchResult(models.Model):
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='results')
    keyword = models.CharField(max_length=255)
    rank = models.IntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    url = models.URLField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.keyword} - Rank {self.rank} - {self.timestamp}"
    



class SearchResult(models.Model):
    isd_date = models.DateField(default=timezone.now)
    isd_time = models.TimeField(default=timezone.now)
    us_date = models.DateField(default=timezone.now)
    us_time = models.TimeField(default=timezone.now)
    day = models.CharField(max_length=10, default="Weekday")
    hour = models.CharField(max_length=20, default="00:00")
    keyword = models.CharField(max_length=100, default="")
    city = models.CharField(max_length=100, default="Unknown")
    link = models.URLField(default="")
    display_link = models.CharField(max_length=200, default="")
    brand_type = models.CharField(max_length=50, default="Unknown")
    spectrum_vs_comp = models.CharField(max_length=50, default="Unknown")
    comp_split = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=200, default="")
    description = models.TextField(default="")
    rank = models.IntegerField(default=0)
    global_rank = models.IntegerField(default=0)
    result_type = models.CharField(max_length=50, default="organic")  # Changed from 'type' to 'result_type'

    def __str__(self):
        return f"{self.keyword} - {self.title} (Rank: {self.rank})"