
import tempfile
import shutil
from io import BytesIO
from PIL import Image

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Post, Comment, Like, Follow

TEMP_MEDIA = tempfile.mkdtemp()


def create_test_image(name='test.jpg', size=(100, 100), color='red'):
    """테스트용 이미지 파일을 생성하는 헬퍼 함수"""
    img = Image.new('RGB', size, color)
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(user=self.user, content='테스트 게시물입니다.')

    def test_post_creation(self):
        """게시물 생성 테스트"""
        self.assertEqual(self.post.content, '테스트 게시물입니다.')
        self.assertEqual(self.post.user, self.user)

    def test_post_str(self):
        """게시물 문자열 표현 테스트"""
        self.assertEqual(str(self.post), 'testuser: 테스트 게시물입니다.')

    def test_post_ordering(self):
        """게시물 정렬 순서 테스트 (최신순)"""
        post2 = Post.objects.create(user=self.user, content='두 번째 게시물')
        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)

    def test_post_default_views(self):
        """게시물 기본 조회수 테스트"""
        self.assertEqual(self.post.views, 0)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class HomeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_welcome_page_for_anonymous(self):
        """비로그인 사용자에게 Welcome 페이지가 표시되는지 테스트"""
        response = self.client.get(reverse('posts:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/welcome.html')
        self.assertContains(response, '로그인')
        self.assertContains(response, '회원가입')

    def test_home_page_status_code(self):
        """로그인 후 홈페이지 접속 테스트"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('posts:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/home.html')

    def test_home_page_displays_posts(self):
        """홈페이지에 게시물이 표시되는지 테스트"""
        Post.objects.create(user=self.user, content='홈 테스트 게시물')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('posts:home'))
        self.assertContains(response, '홈 테스트 게시물')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(user=self.user, content='상세 테스트 게시물')

    def test_detail_page_status_code(self):
        """상세 페이지 접속 테스트"""
        response = self.client.get(reverse('posts:post_detail', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 200)

    def test_detail_page_increases_views(self):
        """상세 페이지 조회 시 조회수 증가 테스트"""
        self.client.get(reverse('posts:post_detail', kwargs={'pk': self.post.pk}))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)

    def test_detail_page_displays_content(self):
        """상세 페이지에 내용이 표시되는지 테스트"""
        response = self.client.get(reverse('posts:post_detail', kwargs={'pk': self.post.pk}))
        self.assertContains(response, '상세 테스트 게시물')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_create_page_status_code(self):
        """게시물 작성 페이지 접속 테스트"""
        response = self.client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_success(self):
        """게시물 작성 성공 테스트 (nonce 검증 포함)"""
        # GET으로 nonce 획득
        get_response = self.client.get(reverse('posts:post_create'))
        nonce = get_response.context['form_nonce']
        response = self.client.post(reverse('posts:post_create'), {
            'content': '새 게시물 작성 테스트',
            'form_nonce': nonce,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(content='새 게시물 작성 테스트').exists())

    def test_create_post_with_image(self):
        """이미지 포함 게시물 작성 테스트"""
        get_response = self.client.get(reverse('posts:post_create'))
        nonce = get_response.context['form_nonce']
        image = create_test_image()
        response = self.client.post(reverse('posts:post_create'), {
            'content': '이미지 포함 게시물',
            'image': image,
            'form_nonce': nonce,
        })
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(content='이미지 포함 게시물')
        self.assertTrue(post.image)

    def test_create_requires_login(self):
        """로그인하지 않은 사용자의 게시물 작성 접근 차단 테스트"""
        self.client.logout()
        response = self.client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.post = Post.objects.create(user=self.user, content='수정 전 내용')
        self.client.login(username='testuser', password='testpass123')

    def test_update_post_success(self):
        """게시물 수정 성공 테스트"""
        response = self.client.post(
            reverse('posts:post_update', kwargs={'pk': self.post.pk}),
            {'content': '수정 후 내용'}
        )
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, '수정 후 내용')

    def test_update_other_user_post(self):
        """다른 사용자의 게시물 수정 시도 테스트"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('posts:post_update', kwargs={'pk': self.post.pk}),
            {'content': '다른 사용자가 수정'}
        )
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, '수정 전 내용')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostDeleteViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.post = Post.objects.create(user=self.user, content='삭제할 게시물')
        self.client.login(username='testuser', password='testpass123')

    def test_delete_post_success(self):
        """게시물 삭제 성공 테스트"""
        response = self.client.post(reverse('posts:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_confirm_page(self):
        """삭제 확인 페이지 접속 테스트"""
        response = self.client.get(reverse('posts:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_other_user_post(self):
        """다른 사용자의 게시물 삭제 시도 테스트"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(reverse('posts:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CommentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.post = Post.objects.create(user=self.user, content='댓글 테스트 게시물')
        self.client.login(username='testuser', password='testpass123')

    def test_create_comment(self):
        """댓글 작성 테스트"""
        response = self.client.post(
            reverse('posts:post_detail', kwargs={'pk': self.post.pk}),
            {'content': '테스트 댓글'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(content='테스트 댓글').exists())

    def test_comment_displayed_on_detail(self):
        """상세 페이지에 댓글이 표시되는지 테스트"""
        Comment.objects.create(post=self.post, user=self.user, content='표시 테스트 댓글')
        response = self.client.get(reverse('posts:post_detail', kwargs={'pk': self.post.pk}))
        self.assertContains(response, '표시 테스트 댓글')

    def test_delete_comment(self):
        """댓글 삭제 테스트"""
        comment = Comment.objects.create(post=self.post, user=self.user, content='삭제할 댓글')
        response = self.client.post(reverse('posts:comment_delete', kwargs={'pk': comment.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_other_user_comment(self):
        """다른 사용자의 댓글 삭제 시도 테스트"""
        comment = Comment.objects.create(post=self.post, user=self.other_user, content='다른 사용자 댓글')
        response = self.client.post(reverse('posts:comment_delete', kwargs={'pk': comment.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LikeToggleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(user=self.user, content='좋아요 테스트 게시물')
        self.client.login(username='testuser', password='testpass123')

    def test_like_post(self):
        """좋아요 추가 테스트"""
        response = self.client.post(reverse('posts:like_toggle', kwargs={'pk': self.post.pk}))
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_unlike_post(self):
        """좋아요 취소 테스트"""
        Like.objects.create(user=self.user, post=self.post)
        response = self.client.post(reverse('posts:like_toggle', kwargs={'pk': self.post.pk}))
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_like_ajax_response(self):
        """AJAX 좋아요 JSON 응답 테스트"""
        response = self.client.post(
            reverse('posts:like_toggle', kwargs={'pk': self.post.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)

    def test_like_requires_login(self):
        """로그인하지 않은 사용자의 좋아요 접근 차단 테스트"""
        self.client.logout()
        response = self.client.post(reverse('posts:like_toggle', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class FollowToggleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.target_user = User.objects.create_user(username='targetuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_follow_user(self):
        """팔로우 테스트"""
        response = self.client.post(reverse('posts:follow_toggle', kwargs={'username': 'targetuser'}))
        self.assertTrue(Follow.objects.filter(follower=self.user, following=self.target_user).exists())

    def test_unfollow_user(self):
        """언팔로우 테스트"""
        Follow.objects.create(follower=self.user, following=self.target_user)
        response = self.client.post(reverse('posts:follow_toggle', kwargs={'username': 'targetuser'}))
        self.assertFalse(Follow.objects.filter(follower=self.user, following=self.target_user).exists())

    def test_follow_self(self):
        """자기 자신 팔로우 시도 테스트"""
        response = self.client.post(reverse('posts:follow_toggle', kwargs={'username': 'testuser'}))
        self.assertFalse(Follow.objects.filter(follower=self.user, following=self.user).exists())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class FollowingFeedTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.followed_user = User.objects.create_user(username='followed', password='testpass123')
        self.unfollowed_user = User.objects.create_user(username='unfollowed', password='testpass123')
        Follow.objects.create(follower=self.user, following=self.followed_user)
        self.client.login(username='testuser', password='testpass123')

    def test_following_feed_status_code(self):
        """팔로잉 피드 페이지 접속 테스트"""
        response = self.client.get(reverse('posts:following_feed'))
        self.assertEqual(response.status_code, 200)

    def test_following_feed_shows_followed_user_posts(self):
        """팔로잉 피드에 팔로우한 사용자의 게시물이 표시되는지 테스트"""
        Post.objects.create(user=self.followed_user, content='팔로우한 사용자의 게시물')
        response = self.client.get(reverse('posts:following_feed'))
        self.assertContains(response, '팔로우한 사용자의 게시물')

    def test_following_feed_hides_unfollowed_user_posts(self):
        """팔로잉 피드에 팔로우하지 않은 사용자의 게시물이 표시되지 않는지 테스트"""
        Post.objects.create(user=self.unfollowed_user, content='팔로우 안한 사용자의 게시물')
        response = self.client.get(reverse('posts:following_feed'))
        self.assertNotContains(response, '팔로우 안한 사용자의 게시물')

    def test_following_feed_requires_login(self):
        """로그인하지 않은 사용자의 팔로잉 피드 접근 차단 테스트"""
        self.client.logout()
        response = self.client.get(reverse('posts:following_feed'))
        self.assertEqual(response.status_code, 302)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LoadMorePostsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        # 10개의 게시물 생성 (페이지당 5개)
        for i in range(10):
            Post.objects.create(user=self.user, content=f'게시물 {i}')

    def test_load_more_first_page(self):
        """첫 번째 페이지 로드 테스트"""
        response = self.client.get(reverse('posts:load_more_posts'), {'page': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['has_next'])

    def test_load_more_last_page(self):
        """마지막 페이지 로드 테스트"""
        response = self.client.get(reverse('posts:load_more_posts'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['has_next'])

    def test_load_more_beyond_pages(self):
        """존재하지 않는 페이지 로드 테스트"""
        response = self.client.get(reverse('posts:load_more_posts'), {'page': 100})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['html'], '')
        self.assertFalse(data['has_next'])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()