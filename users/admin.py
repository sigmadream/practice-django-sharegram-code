from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio_preview', 'profile_image']
    search_fields = ['user__username', 'bio']

    def bio_preview(self, obj):
        return obj.bio[:50] if obj.bio else '-'
    bio_preview.short_description = '자기소개'