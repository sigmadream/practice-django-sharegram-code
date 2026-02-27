from django.contrib.auth.models import User
from django.db import models

class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')
    url = models.URLField(verbose_name='URL')
    title = models.CharField(max_length=200, blank=True, verbose_name='제목')
    description = models.TextField(blank=True, verbose_name='설명')
    og_image = models.URLField(blank=True, verbose_name='OG 이미지 URL')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '링크'
        verbose_name_plural = '링크'

    def __str__(self):
        return self.title or self.url
