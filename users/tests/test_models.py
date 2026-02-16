import pytest
from django.contrib.auth.models import User
from users.models import Profile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import tempfile
import os

@pytest.mark.django_db
def test_profile_created_on_user_creation(user_factory):
    user = user_factory(username="tdduser")
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_profile_str_returns_username_profile(user_factory):
    user = user_factory(username="tdduser2")
    profile = user.profile
    assert str(profile) == "tdduser2의 프로필"


@pytest.mark.django_db
def test_bio_max_length(user_factory):
    user = user_factory(username="bio_user")
    profile = user.profile
    profile.bio = "a" * 501
    with pytest.raises(Exception):
        profile.save()

@pytest.mark.django_db
def test_profile_image_resized_on_save(settings, user_factory, tmp_path):
    user = user_factory(username="imguser")
    # tmp_path 활용: pytest-django에서 제공하는 임시 폴더 fixture
    orig_size = (2000, 2000)
    color = (255, 0, 0)
    image_file = io.BytesIO()
    image = Image.new("RGB", orig_size, color)
    image.save(image_file, format='JPEG')
    image_file.seek(0)

    img_name = "test.jpg"
    uploaded = SimpleUploadedFile(img_name, image_file.read(), content_type="image/jpeg")
    user.profile.profile_image.save(img_name, uploaded)
    user.profile.save()

    img = Image.open(user.profile.profile_image.path)
    assert img.height <= 300 and img.width <= 300

@pytest.mark.django_db
def test_profile_deleted_with_user(user_factory):
    user = user_factory(username="to_delete")
    profile_pk = user.profile.pk
    user.delete()
    assert not Profile.objects.filter(pk=profile_pk).exists()            
