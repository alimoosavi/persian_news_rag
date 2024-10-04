import uuid
from django.db import models
import datetime
from urllib.parse import urljoin


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NewsSource(BaseModel):
    name = models.CharField(max_length=255)
    base_url = models.URLField(max_length=500)

    def __str__(self):
        return self.name


class NewsLink(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(NewsSource, on_delete=models.DO_NOTHING, related_name='links')
    news_link = models.CharField(max_length=400)
    date = models.DateTimeField(default=datetime.datetime.now)
    has_processed = models.BooleanField(default=False)

    def get_full_url(self):
        return urljoin(self.source.base_url, self.news_link)


class News(BaseModel):
    news_source = models.CharField(max_length=255)
    date = models.DateTimeField(default=datetime.datetime.now)
    news_link = models.CharField(max_length=400)
    title = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('news_source', 'news_link',)
