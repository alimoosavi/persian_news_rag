import uuid
from django.db import models
import datetime


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


class NewsCategory(BaseModel):
    category_id = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    source = models.ForeignKey('NewsSource', on_delete=models.DO_NOTHING, to_field='id')

    class Meta:
        unique_together = ('category_name', 'category_id')


class NewsLink(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey('NewsCategory', on_delete=models.DO_NOTHING, to_field='id')
    news_link = models.CharField(max_length=400)
    date = models.DateTimeField(default=datetime.datetime.now)
    has_processed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('category', 'news_link')


class News(BaseModel):
    news_link = models.ForeignKey('NewsLink', on_delete=models.DO_NOTHING, to_field='id')
    title = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.title
