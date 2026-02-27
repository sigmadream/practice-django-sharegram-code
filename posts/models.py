# posts/models.py

import os
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from PIL import Image


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(max_length=500, verbose_name="내용")
    image = models.ImageField(
        upload_to="post_images/", blank=True, verbose_name="이미지"
    )
    thumbnail = models.ImageField(
        upload_to="post_thumbnails/", blank=True, verbose_name="썸네일"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="조회수")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "게시물"
        verbose_name_plural = "게시물"

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            try:
                old_post = Post.objects.get(pk=self.pk)
                image_changed = old_post.image != self.image
            except Post.DoesNotExist:
                image_changed = True
        else:
            image_changed = True

        super().save(*args, **kwargs)

        if image_changed and self.image:
            self._generate_thumbnail()

    def _generate_thumbnail(self):
        try:
            img = Image.open(self.image.path)
            img.thumbnail((300, 300))
            thumb_io = BytesIO()
            img_format = img.format or "JPEG"
            img.save(thumb_io, format=img_format)
            thumb_io.seek(0)
            thumb_name = f"thumb_{os.path.basename(self.image.name)}"
            self.thumbnail.save(thumb_name, ContentFile(thumb_io.read()), save=False)
            Post.objects.filter(pk=self.pk).update(thumbnail=self.thumbnail.name)
        except (FileNotFoundError, ValueError):
            pass


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=200, verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "댓글"
        verbose_name_plural = "댓글"

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_like")
        ]
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요"

    def __str__(self):
        return f"{self.user.username} → {self.post.content[:20]}"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow')
        ]
        verbose_name = '팔로우'
        verbose_name_plural = '팔로우'

    def __str__(self):
        return f'{self.follower.username} → {self.following.username}'
