import tempfile
import shutil
from io import BytesIO
from PIL import Image

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Profile

TEMP_MEDIA = tempfile.mkdtemp()


def create_test_image(name='test.jpg', size=(100, 100), color='red'):
    """테스트용 이미지 파일을 생성하는 헬퍼 함수"""
    img = Image.new('RGB', size, color)
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_profile_auto_created(self):
        """사용자 생성 시 프로필이 자동으로 생성되는지 테스트"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_str(self):
        """프로필의 문자열 표현 테스트"""
        self.assertEqual(str(self.user.profile), 'testuser의 프로필')

    def test_profile_default_image(self):
        """프로필의 기본 이미지 설정 테스트"""
        self.assertEqual(self.user.profile.profile_image, 'default.jpg')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


class RegisterViewTest(TestCase):
    def test_register_page_status_code(self):
        """회원가입 페이지 접속 테스트"""
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_form_display(self):
        """회원가입 폼 표시 테스트"""
        response = self.client.get(reverse('users:register'))
        self.assertContains(response, '회원가입')

    def test_register_success(self):
        """회원가입 성공 테스트"""
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        """비밀번호 불일치 시 회원가입 실패 테스트"""
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'complexpass123!',
            'password2': 'differentpass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_login_page_status_code(self):
        """로그인 페이지 접속 테스트"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """로그인 성공 테스트"""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_logout(self):
        """로그아웃 테스트"""
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 200)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_profile_page(self):
        """프로필 페이지 접속 테스트"""
        response = self.client.get(reverse('users:profile', kwargs={'username': 'testuser'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@test.com')
        self.client.login(username='testuser', password='testpass123')

    def test_edit_profile_page(self):
        """프로필 수정 페이지 접속 테스트"""
        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_success(self):
        """프로필 수정 성공 테스트"""
        response = self.client.post(reverse('users:edit_profile'), {
            'username': 'updateduser',
            'email': 'updated@test.com',
            'bio': 'Hello!',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')

    def test_edit_profile_requires_login(self):
        """로그인하지 않은 사용자의 프로필 수정 접근 차단 테스트"""
        self.client.logout()
        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()
