import pytest
from django.contrib.auth.models import User

@pytest.fixture
def user_factory(db):
    def create_user(**kwargs):
        return User.objects.create_user(password='pw', **kwargs)
    return create_user