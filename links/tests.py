import tempfile
import shutil
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Link
from .utils import fetch_og_metadata

TEMP_MEDIA = tempfile.mkdtemp()


class FetchOgMetadataTest(TestCase):
    @patch('links.utils.requests.get')
    def test_fetch_og_metadata_success(self, mock_get):
        """OG 메타데이터 크롤링 성공 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
        <head>
            <meta property="og:title" content="테스트 제목">
            <meta property="og:description" content="테스트 설명">
            <meta property="og:image" content="https://example.com/image.jpg">
        </head>
        <body></body>
        </html>
        '''
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_og_metadata('https://example.com')
        self.assertEqual(result['title'], '테스트 제목')
        self.assertEqual(result['description'], '테스트 설명')
        self.assertEqual(result['image'], 'https://example.com/image.jpg')

    @patch('links.utils.requests.get')
    def test_fetch_og_metadata_fallback(self, mock_get):
        """OG 태그가 없을 때 일반 태그로 대체하는 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
        <head>
            <title>대체 제목</title>
            <meta name="description" content="대체 설명">
        </head>
        <body></body>
        </html>
        '''
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_og_metadata('https://example.com')
        self.assertEqual(result['title'], '대체 제목')
        self.assertEqual(result['description'], '대체 설명')

    @patch('links.utils.requests.get')
    def test_fetch_og_metadata_failure(self, mock_get):
        """크롤링 실패 시 빈 결과 반환 테스트"""
        mock_get.side_effect = Exception('Connection error')
        result = fetch_og_metadata('https://example.com')
        self.assertEqual(result['title'], '')
        self.assertEqual(result['description'], '')
        self.assertEqual(result['image'], '')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LinkModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.link = Link.objects.create(
            user=self.user,
            url='https://example.com',
            title='예제 사이트',
            description='테스트 설명'
        )

    def test_link_creation(self):
        """링크 생성 테스트"""
        self.assertEqual(self.link.title, '예제 사이트')
        self.assertEqual(self.link.user, self.user)

    def test_link_str(self):
        """링크 문자열 표현 테스트"""
        self.assertEqual(str(self.link), '예제 사이트')

    def test_link_str_without_title(self):
        """제목이 없는 링크의 문자열 표현 테스트"""
        link = Link.objects.create(user=self.user, url='https://test.com')
        self.assertEqual(str(link), 'https://test.com')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LinkListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_link_list_status_code(self):
        """링크 목록 페이지 접속 테스트"""
        response = self.client.get(reverse('links:link_list'))
        self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LinkDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.link = Link.objects.create(user=self.user, url='https://example.com', title='테스트')

    def test_link_detail_status_code(self):
        """링크 상세 페이지 접속 테스트"""
        response = self.client.get(reverse('links:link_detail', kwargs={'pk': self.link.pk}))
        self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LinkCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    @patch('links.views.fetch_og_metadata')
    def test_create_link_success(self, mock_fetch):
        """링크 생성 성공 테스트"""
        mock_fetch.return_value = {
            'title': '크롤링된 제목',
            'description': '크롤링된 설명',
            'image': 'https://example.com/image.jpg'
        }
        response = self.client.post(reverse('links:link_create'), {
            'url': 'https://example.com'
        })
        self.assertEqual(response.status_code, 302)
        link = Link.objects.get(url='https://example.com')
        self.assertEqual(link.title, '크롤링된 제목')

    def test_create_link_requires_login(self):
        """로그인하지 않은 사용자의 링크 생성 접근 차단 테스트"""
        self.client.logout()
        response = self.client.get(reverse('links:link_create'))
        self.assertEqual(response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LinkDeleteViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.link = Link.objects.create(user=self.user, url='https://example.com', title='삭제 테스트')
        self.client.login(username='testuser', password='testpass123')

    def test_delete_link_success(self):
        """링크 삭제 성공 테스트"""
        response = self.client.post(reverse('links:link_delete', kwargs={'pk': self.link.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Link.objects.filter(pk=self.link.pk).exists())

    def test_delete_other_user_link(self):
        """다른 사용자의 링크 삭제 시도 테스트"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(reverse('links:link_delete', kwargs={'pk': self.link.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Link.objects.filter(pk=self.link.pk).exists())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()
