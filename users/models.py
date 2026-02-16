from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Length
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from PIL import Image

models.TextField.register_lookup(Length)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, verbose_name='자기소개')
    profile_image = models.ImageField(default='default.jpg', upload_to='profile_pics', verbose_name='프로필 이미지')

    class Meta:
        verbose_name = '프로필'
        verbose_name_plural = '프로필'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(bio__length__lte=500),
                name="profile_bio_max_length",
            ),
        ]

    def __str__(self):
        return f'{self.user.username}의 프로필'

    def clean(self):
        super().clean()
        if len(self.bio) > 500:
            raise ValidationError({"bio": ["자기소개는 최대 500자까지 입력 가능합니다."]})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        try:
            img = Image.open(self.profile_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_image.path)
        except (FileNotFoundError, ValueError):
            pass


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
